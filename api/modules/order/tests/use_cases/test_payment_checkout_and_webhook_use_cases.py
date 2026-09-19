"""Checkout creation, webhook validation and superseded-checkout cancellation."""
from datetime import datetime, timezone
from decimal import Decimal
from uuid import uuid4

import pytest

from modules.order.application.ports.driven.payment_provider import (
    CancelCheckoutResult,
    CreateCheckoutResult,
    PaymentProviderError,
    ProviderPayment,
)
from modules.order.application.ports.driver.payment_ports import (
    CancelSupersededCheckoutCommand,
    CreatePaymentCheckoutCommand,
    HandlePaymentWebhookCommand,
)
from modules.order.application.use_cases.cancel_superseded_checkout_use_case import (
    CancelSupersededCheckoutUseCase,
)
from modules.order.application.use_cases.create_payment_checkout_use_case import (
    CreatePaymentCheckoutUseCase,
)
from modules.order.application.use_cases.handle_payment_webhook_use_case import (
    HandlePaymentWebhookUseCase,
)
from modules.order.domain.errors.order_errors import (
    OnlinePaymentRequiredError,
    OrderNotConfirmedError,
    OrderStateError,
    PaymentAttemptNotFoundError,
    PaymentTypeRequiredError,
)
from modules.order.domain.models.cancellation_status import CancellationStatus
from modules.order.domain.models.order import Order
from modules.order.domain.models.order_state import OrderState
from modules.order.domain.models.payment_attempt import PaymentAttempt
from modules.order.domain.models.payment_method import PaymentMethod
from modules.order.domain.models.payment_status import PaymentStatus

NOW = datetime(2026, 9, 17, tzinfo=timezone.utc)


class FakeOrderRepo:
    def __init__(self, order):
        self.order = order
        self.saves = 0

    def get_by_id(self, order_id):
        return self.order

    def save(self, order):
        self.order = order
        self.saves += 1
        return order


class FakeAttemptRepo:
    def __init__(self):
        self.attempts = []

    def create_for_version(
        self,
        *,
        order_id,
        provider,
        amount,
        order_version,
        external_reference,
        create_idempotency_key,
        attempt_id=None,
    ):
        attempt = PaymentAttempt(
            id=attempt_id or str(uuid4()),
            order_id=order_id,
            provider=provider,
            amount=amount,
            status=PaymentStatus.PENDING,
            order_version=order_version,
            external_reference=external_reference,
            create_idempotency_key=create_idempotency_key,
        )
        self.attempts.append(attempt)
        return attempt

    def find_current_for_version(self, order_id, version):
        for attempt in self.attempts:
            if attempt.order_id == order_id and attempt.order_version == version:
                if not attempt.superseded:
                    return attempt
        return None

    def save(self, attempt):
        return attempt

    def get_by_id(self, attempt_id):
        return next((a for a in self.attempts if a.id == attempt_id), None)

    def add(self, attempt):
        self.attempts.append(attempt)
        return attempt

    def get_by_external_id(self, external_id):
        return next((a for a in self.attempts if a.external_id == external_id), None)


class FakeProvider:
    def __init__(self, create_error=False, cancel_result=None, remote_payment=None):
        self.create_error = create_error
        self.cancel_result = cancel_result or CancelCheckoutResult()
        self.remote_payment = remote_payment
        self.create_calls = []
        self.cancel_calls = []

    def create_checkout(self, request):
        self.create_calls.append(request)
        if self.create_error:
            raise PaymentProviderError("timeout")
        return CreateCheckoutResult(
            external_id="MP-1",
            checkout_url="https://mp/checkout",
            external_reference=request.external_reference,
        )

    def cancel_checkout(self, request):
        self.cancel_calls.append(request)
        return self.cancel_result

    def get_payment(self, external_id):
        return self.remote_payment


def make_order(
    status=OrderState.PENDING,
    payment_type=PaymentMethod.ONLINE,
    version=5,
    total=Decimal("1000"),
) -> Order:
    return Order(
        id="o-1",
        status=status,
        subtotal=total,
        discount=Decimal("0"),
        total_amount=total,
        payment_type=payment_type,
        version=version,
        business_config_id="b-1",
        conversation_id="c-1",
    )


def _checkout_use_case(order, provider):
    order_repo = FakeOrderRepo(order)
    attempt_repo = FakeAttemptRepo()
    use_case = CreatePaymentCheckoutUseCase(
        order_repo=order_repo,
        payment_repo=attempt_repo,
        payment_provider=provider,
    )
    return use_case, order_repo, attempt_repo


def test_checkout_creates_one_attempt_and_persists_the_provider_key():
    provider = FakeProvider()
    use_case, _, attempt_repo = _checkout_use_case(make_order(), provider)

    result = use_case.execute(CreatePaymentCheckoutCommand(order_id="o-1"))

    assert result.created is True
    assert result.checkout_url == "https://mp/checkout"
    assert result.order_version == 5
    assert len(attempt_repo.attempts) == 1
    assert attempt_repo.attempts[0].external_id == "MP-1"
    assert provider.create_calls[0].idempotency_key == attempt_repo.attempts[0].create_idempotency_key


def test_checkout_replays_an_existing_current_attempt_without_calling_the_provider():
    provider = FakeProvider()
    order = make_order()
    use_case, _, attempt_repo = _checkout_use_case(order, provider)
    attempt_repo.add(
        PaymentAttempt(
            id="a-1",
            order_id="o-1",
            provider="MERCADOPAGO",
            amount=Decimal("1000"),
            status=PaymentStatus.PENDING,
            order_version=5,
            external_id="MP-EXISTING",
            checkout_url="https://mp/existing",
        )
    )

    result = use_case.execute(CreatePaymentCheckoutCommand(order_id="o-1"))

    assert result.created is False
    assert result.checkout_url == "https://mp/existing"
    assert provider.create_calls == []


def test_checkout_timeout_retry_reuses_the_same_attempt_and_key():
    provider = FakeProvider(create_error=True)
    use_case, _, attempt_repo = _checkout_use_case(make_order(), provider)

    with pytest.raises(PaymentProviderError):
        use_case.execute(CreatePaymentCheckoutCommand(order_id="o-1"))
    with pytest.raises(PaymentProviderError):
        use_case.execute(CreatePaymentCheckoutCommand(order_id="o-1"))

    assert len(attempt_repo.attempts) == 1
    keys = [call.idempotency_key for call in provider.create_calls]
    assert len(keys) == 2
    assert keys[0] == keys[1]


@pytest.mark.parametrize(
    "order",
    [
        make_order(status=OrderState.DRAFT),
        make_order(payment_type=PaymentMethod.CASH),
        make_order(total=Decimal("0")),
    ],
)
def test_checkout_rejects_invalid_orders(order):
    provider = FakeProvider()
    use_case, _, attempt_repo = _checkout_use_case(order, provider)

    with pytest.raises(OrderStateError):
        use_case.execute(CreatePaymentCheckoutCommand(order_id="o-1"))

    assert attempt_repo.attempts == []
    assert provider.create_calls == []


def test_checkout_without_payment_type_is_a_payment_type_required_business_error():
    provider = FakeProvider()
    use_case, _, attempt_repo = _checkout_use_case(
        make_order(payment_type=None), provider
    )

    with pytest.raises(PaymentTypeRequiredError):
        use_case.execute(CreatePaymentCheckoutCommand(order_id="o-1"))

    assert attempt_repo.attempts == []
    assert provider.create_calls == []


def test_checkout_cash_order_is_an_online_payment_required_business_error():
    provider = FakeProvider()
    use_case, _, _ = _checkout_use_case(
        make_order(payment_type=PaymentMethod.CASH), provider
    )

    with pytest.raises(OnlinePaymentRequiredError):
        use_case.execute(CreatePaymentCheckoutCommand(order_id="o-1"))

    assert provider.create_calls == []


def test_checkout_draft_order_is_an_order_not_confirmed_business_error():
    provider = FakeProvider()
    use_case, _, _ = _checkout_use_case(make_order(status=OrderState.DRAFT), provider)

    with pytest.raises(OrderNotConfirmedError):
        use_case.execute(CreatePaymentCheckoutCommand(order_id="o-1"))

    assert provider.create_calls == []


def _webhook_use_case(order, attempt, remote):
    order_repo = FakeOrderRepo(order)
    attempt_repo = FakeAttemptRepo()
    attempt_repo.add(attempt)
    use_case = HandlePaymentWebhookUseCase(
        order_repo=order_repo,
        payment_repo=attempt_repo,
        payment_provider=FakeProvider(remote_payment=remote),
    )
    return use_case, order_repo, attempt_repo


def _current_attempt(order_version=5, amount=Decimal("1000")):
    return PaymentAttempt(
        id="a-1",
        order_id="o-1",
        provider="MERCADOPAGO",
        amount=amount,
        status=PaymentStatus.PENDING,
        order_version=order_version,
        external_id="MP-1",
    )


def _webhook_command():
    return HandlePaymentWebhookCommand(
        provider="MERCADOPAGO",
        data_id="MP-1",
        topic="payment",
        raw_payload={},
        headers={},
    )


def test_current_version_approved_pays_the_order():
    order = make_order()
    attempt = _current_attempt()
    remote = ProviderPayment(
        external_id="MP-1", status=PaymentStatus.APPROVED, amount=Decimal("1000")
    )
    use_case, order_repo, _ = _webhook_use_case(order, attempt, remote)

    result = use_case.execute(_webhook_command())

    assert result.applied is True
    assert order_repo.order.status is OrderState.PAID


def test_stale_version_approved_records_status_but_does_not_pay():
    order = make_order(version=6)
    attempt = _current_attempt(order_version=5)
    remote = ProviderPayment(
        external_id="MP-1", status=PaymentStatus.APPROVED, amount=Decimal("1000")
    )
    use_case, order_repo, attempt_repo = _webhook_use_case(order, attempt, remote)

    result = use_case.execute(_webhook_command())

    assert result.applied is False
    assert order_repo.order.status is OrderState.PENDING
    assert attempt_repo.attempts[0].status is PaymentStatus.APPROVED
    assert attempt_repo.attempts[0].superseded_at is None


def test_wrong_amount_does_not_pay():
    order = make_order(total=Decimal("2000"))
    attempt = _current_attempt(amount=Decimal("1000"))
    remote = ProviderPayment(
        external_id="MP-1", status=PaymentStatus.APPROVED, amount=Decimal("1000")
    )
    use_case, order_repo, _ = _webhook_use_case(order, attempt, remote)

    result = use_case.execute(_webhook_command())

    assert result.applied is False
    assert order_repo.order.status is OrderState.PENDING


def test_superseded_attempt_does_not_pay():
    order = make_order()
    attempt = _current_attempt()
    attempt.supersede(NOW)
    remote = ProviderPayment(
        external_id="MP-1", status=PaymentStatus.APPROVED, amount=Decimal("1000")
    )
    use_case, order_repo, _ = _webhook_use_case(order, attempt, remote)

    result = use_case.execute(_webhook_command())

    assert result.applied is False
    assert order_repo.order.status is OrderState.PENDING


def test_non_approved_notification_keeps_the_order_pending():
    order = make_order()
    attempt = _current_attempt()
    remote = ProviderPayment(
        external_id="MP-1", status=PaymentStatus.REJECTED, amount=Decimal("1000")
    )
    use_case, order_repo, _ = _webhook_use_case(order, attempt, remote)

    result = use_case.execute(_webhook_command())

    assert result.applied is False
    assert order_repo.order.status is OrderState.PENDING


def test_duplicate_final_notification_is_idempotent():
    order = make_order()
    attempt = _current_attempt()
    attempt.status = PaymentStatus.APPROVED
    remote = ProviderPayment(
        external_id="MP-1", status=PaymentStatus.APPROVED, amount=Decimal("1000")
    )
    use_case, order_repo, _ = _webhook_use_case(order, attempt, remote)

    first = use_case.execute(_webhook_command())
    second = use_case.execute(_webhook_command())

    assert first.applied is True
    assert second.applied is False
    assert order_repo.order.status is OrderState.PAID


def test_unknown_attempt_raises():
    order = make_order()
    remote = ProviderPayment(
        external_id="MP-UNKNOWN", status=PaymentStatus.APPROVED, amount=Decimal("1000")
    )
    order_repo = FakeOrderRepo(order)
    use_case = HandlePaymentWebhookUseCase(
        order_repo=order_repo,
        payment_repo=FakeAttemptRepo(),
        payment_provider=FakeProvider(remote_payment=remote),
    )

    with pytest.raises(PaymentAttemptNotFoundError):
        use_case.execute(_webhook_command())


def _cancel_use_case(attempt, provider):
    repo = FakeAttemptRepo()
    repo.add(attempt)
    use_case = CancelSupersededCheckoutUseCase(
        payment_repo=repo, payment_provider=provider
    )
    return use_case, repo


def test_cancel_reuses_a_persisted_key_and_marks_cancelled():
    attempt = _current_attempt()
    attempt.supersede(NOW)
    attempt.cancel_idempotency_key = "cancel-key"
    provider = FakeProvider()
    use_case, _ = _cancel_use_case(attempt, provider)

    result = use_case.execute(CancelSupersededCheckoutCommand(payment_attempt_id="a-1"))

    assert result.cancellation_status == CancellationStatus.CANCELLED.value
    assert provider.cancel_calls[0].idempotency_key == "cancel-key"
    assert provider.cancel_calls[0].external_id == "MP-1"


def test_cancel_generates_and_persists_a_key_when_missing():
    attempt = _current_attempt()
    attempt.supersede(NOW)
    provider = FakeProvider()
    use_case, _ = _cancel_use_case(attempt, provider)

    use_case.execute(CancelSupersededCheckoutCommand(payment_attempt_id="a-1"))

    assert attempt.cancel_idempotency_key is not None
    assert provider.cancel_calls[0].idempotency_key == attempt.cancel_idempotency_key


def test_cancel_reports_already_cancelled_idempotently():
    attempt = _current_attempt()
    attempt.supersede(NOW)
    provider = FakeProvider(cancel_result=CancelCheckoutResult(already_cancelled=True))
    use_case, _ = _cancel_use_case(attempt, provider)

    result = use_case.execute(CancelSupersededCheckoutCommand(payment_attempt_id="a-1"))

    assert result.already_cancelled is True
    assert result.cancellation_status == CancellationStatus.REMOTE_ALREADY_CANCELLED.value


def test_cancel_marks_failed_on_provider_error_without_raising():
    attempt = _current_attempt()
    attempt.supersede(NOW)

    class FailingProvider(FakeProvider):
        def cancel_checkout(self, request):
            raise PaymentProviderError("timeout")

    use_case, _ = _cancel_use_case(attempt, FailingProvider())

    result = use_case.execute(CancelSupersededCheckoutCommand(payment_attempt_id="a-1"))

    assert result.cancellation_status == CancellationStatus.FAILED.value


def test_cancel_requires_a_superseded_attempt():
    attempt = _current_attempt()
    use_case, _ = _cancel_use_case(attempt, FakeProvider())

    with pytest.raises(OrderStateError):
        use_case.execute(CancelSupersededCheckoutCommand(payment_attempt_id="a-1"))


def test_cancel_without_remote_checkout_needs_nothing():
    attempt = _current_attempt()
    attempt.external_id = None
    attempt.supersede(NOW)
    provider = FakeProvider()
    use_case, _ = _cancel_use_case(attempt, provider)

    result = use_case.execute(CancelSupersededCheckoutCommand(payment_attempt_id="a-1"))

    assert result.cancellation_status == CancellationStatus.NOT_REQUIRED.value
    assert provider.cancel_calls == []
