from decimal import Decimal

import pytest

from modules.order.application.ports.driver.payment_ports import (
    ProcessPaymentNotificationCommand,
)
from modules.order.application.ports.driven.payment_provider import ProviderPayment
from modules.order.application.use_cases.process_payment_notification_use_case import (
    ProcessPaymentNotificationUseCase,
)
from modules.order.domain.models.order import Order
from modules.order.domain.models.order_state import OrderState
from modules.order.domain.models.payment import Payment
from modules.order.domain.models.payment_status import PaymentStatus


class FakeOrderRepository:
    def __init__(self, order, events):
        self.order = order
        self.events = events
        self.saved = []

    def get_by_id(self, order_id):
        self.events.append("order.get")
        return self.order if self.order and self.order.id == order_id else None

    def save(self, order):
        self.events.append("order.save")
        self.saved.append(order)
        self.order = order
        return order


class FakePaymentRepository:
    def __init__(self, payment, events):
        self.payment = payment
        self.events = events
        self.lookup_calls = []
        self.updated = []

    def create_pending(self, order_id, provider, amount, external_reference):
        raise AssertionError("notification processing must not create payments")

    def save(self, payment):
        self.payment = payment
        return payment

    def get_by_external_id(self, external_id):
        self.events.append("payment.get_external")
        self.lookup_calls.append(("external_id", external_id))
        return self.payment if self.payment.external_id == external_id else None

    def get_by_preference_id(self, preference_id):
        self.events.append("payment.get_preference")
        self.lookup_calls.append(("preference_id", preference_id))
        return self.payment if self.payment.preference_id == preference_id else None

    def get_by_external_reference(self, external_reference):
        self.events.append("payment.get_reference")
        self.lookup_calls.append(("external_reference", external_reference))
        return self.payment if self.payment.external_reference == external_reference else None

    def update_status(self, payment_id, status):
        self.events.append("payment.update_status")
        self.updated.append((payment_id, status))
        self.payment.status = status
        return self.payment


class FakePaymentProvider:
    def __init__(self, remote_payment, events):
        self.remote_payment = remote_payment
        self.events = events
        self.requests = []

    def create_checkout_link(self, request):
        raise AssertionError("notification processing must not create checkout links")

    def get_payment(self, external_id):
        self.events.append("provider.get_payment")
        self.requests.append(external_id)
        return self.remote_payment


def make_order(status=OrderState.PENDING):
    return Order(
        id="order-1",
        status=status,
        subtotal=Decimal("1500.00"),
        discount=Decimal("0"),
        total_amount=Decimal("1500.00"),
    )


def make_payment(status=PaymentStatus.PENDING):
    return Payment(
        id="payment-1",
        order_id="order-1",
        provider="MERCADOPAGO",
        amount=Decimal("1500.00"),
        status=status,
        external_id="mp-1",
        preference_id="pref-1",
        external_reference="order-1",
    )


def make_command(data_id="mp-1"):
    return ProcessPaymentNotificationCommand(
        provider="MERCADOPAGO",
        data_id=data_id,
        topic="payment",
        raw_payload={"status": "rejected"},
        headers={"x-test": "1"},
    )


def make_use_case(remote_payment, local_payment, order):
    events = []
    payment_repo = FakePaymentRepository(local_payment, events)
    order_repo = FakeOrderRepository(order, events)
    provider = FakePaymentProvider(remote_payment, events)
    return (
        ProcessPaymentNotificationUseCase(
            order_repo=order_repo,
            payment_repo=payment_repo,
            payment_provider=provider,
        ),
        payment_repo,
        order_repo,
        provider,
        events,
    )


def test_fetches_authoritative_provider_payment_before_local_mutation():
    remote = ProviderPayment(
        external_id="mp-1",
        status=PaymentStatus.APPROVED,
        preference_id="pref-1",
        external_reference="order-1",
    )
    use_case, payment_repo, order_repo, provider, events = make_use_case(
        remote, make_payment(), make_order()
    )

    result = use_case.execute(make_command(data_id="payload-id"))

    assert provider.requests == ["payload-id"]
    assert events.index("provider.get_payment") < events.index("payment.update_status")
    assert payment_repo.updated == [("payment-1", PaymentStatus.APPROVED)]
    assert len(order_repo.saved) == 1
    assert result.payment_id == "payment-1"
    assert result.status == "APPROVED"
    assert result.order_status == "PAID"
    assert result.processed is True


@pytest.mark.parametrize(
    "status",
    [PaymentStatus.REJECTED, PaymentStatus.FAILED, PaymentStatus.EXPIRED],
)
def test_non_approved_payment_updates_payment_and_keeps_order_pending(status):
    remote = ProviderPayment(
        external_id="mp-1",
        status=status,
        preference_id="pref-1",
        external_reference="order-1",
    )
    use_case, payment_repo, order_repo, _, _ = make_use_case(
        remote, make_payment(), make_order()
    )

    result = use_case.execute(make_command())

    assert payment_repo.updated == [("payment-1", status)]
    assert order_repo.order.status == OrderState.PENDING
    assert order_repo.saved == []
    assert result.status == status.value
    assert result.order_status == "PENDING"


def test_falls_back_to_preference_id_and_external_reference_lookup():
    remote = ProviderPayment(
        external_id="mp-new",
        status=PaymentStatus.APPROVED,
        preference_id="pref-1",
        external_reference="order-1",
    )
    use_case, payment_repo, _, _, _ = make_use_case(remote, make_payment(), make_order())

    result = use_case.execute(make_command(data_id="mp-new"))

    assert payment_repo.lookup_calls[:2] == [
        ("external_id", "mp-new"),
        ("preference_id", "pref-1"),
    ]
    assert result.order_status == "PAID"

    remote_without_preference = ProviderPayment(
        external_id="mp-other",
        status=PaymentStatus.APPROVED,
        external_reference="order-1",
    )
    use_case, payment_repo, _, _, _ = make_use_case(
        remote_without_preference, make_payment(), make_order()
    )

    result = use_case.execute(make_command(data_id="mp-other"))

    assert payment_repo.lookup_calls == [
        ("external_id", "mp-other"),
        ("external_reference", "order-1"),
    ]
    assert result.order_status == "PAID"


def test_duplicate_final_notification_is_idempotent_without_duplicate_effects():
    remote = ProviderPayment(
        external_id="mp-1",
        status=PaymentStatus.APPROVED,
        preference_id="pref-1",
        external_reference="order-1",
    )
    use_case, payment_repo, order_repo, provider, _ = make_use_case(
        remote, make_payment(status=PaymentStatus.APPROVED), make_order(status=OrderState.PAID)
    )

    result = use_case.execute(make_command())

    assert provider.requests == ["mp-1"]
    assert payment_repo.updated == []
    assert order_repo.saved == []
    assert result.status == "APPROVED"
    assert result.order_status == "PAID"
    assert result.processed is True
