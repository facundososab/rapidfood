from decimal import Decimal

import pytest

from modules.order.application.ports.driver.payment_ports import CreatePaymentLinkCommand
from modules.order.application.ports.driven.payment_provider import CreateCheckoutLinkResult
from modules.order.application.use_cases.create_payment_link_use_case import (
    CreatePaymentLinkUseCase,
)
from modules.order.domain.errors.order_errors import OrderNotFound, OrderStateError
from modules.order.domain.models.order import Order
from modules.order.domain.models.order_state import OrderState
from modules.order.domain.models.payment import Payment
from modules.order.domain.models.payment_method import PaymentMethod
from modules.order.domain.models.payment_status import PaymentStatus


class FakeOrderRepository:
    def __init__(self, order=None):
        self.order = order

    def get_by_id(self, order_id):
        return self.order if self.order and self.order.id == order_id else None

    def save(self, order):
        self.order = order
        return order


class FakePaymentRepository:
    def __init__(self, reject_create=True):
        self.reject_create = reject_create
        self.created = []
        self.saved = []

    def create_pending(self, order_id, provider, amount, external_reference):
        if self.reject_create:
            raise AssertionError("payment should not be created for invalid orders")
        payment = Payment(
            id="payment-1",
            order_id=order_id,
            provider=provider,
            amount=amount,
            status=PaymentStatus.PENDING,
            external_reference=external_reference,
        )
        self.created.append(payment)
        return payment

    def save(self, payment):
        self.saved.append(payment)
        return payment


class FakePaymentProvider:
    def __init__(self, reject_create=True):
        self.reject_create = reject_create
        self.requests = []

    def create_checkout_link(self, request):
        self.requests.append(request)
        if self.reject_create:
            raise AssertionError("provider should not be called for invalid orders")
        return CreateCheckoutLinkResult(
            preference_id="pref-1",
            checkout_url="https://pay.example/checkout",
            external_reference=request.external_reference,
            external_id="external-1",
        )


def make_order(
    status=OrderState.PENDING,
    payment_type=PaymentMethod.ONLINE,
    total_amount=Decimal("1500.00"),
):
    return Order(
        id="order-1",
        status=status,
        subtotal=total_amount or Decimal("0"),
        discount=Decimal("0"),
        payment_type=payment_type,
        total_amount=total_amount,
    )


def make_use_case(order):
    return CreatePaymentLinkUseCase(
        order_repo=FakeOrderRepository(order),
        payment_repo=FakePaymentRepository(),
        payment_provider=FakePaymentProvider(),
    )


def test_rejects_missing_order_before_creating_provider_link():
    use_case = make_use_case(order=None)

    with pytest.raises(OrderNotFound):
        use_case.execute(CreatePaymentLinkCommand(order_id="missing"))


def test_rejects_order_that_is_not_pending_before_creating_provider_link():
    use_case = make_use_case(make_order(status=OrderState.DRAFT))

    with pytest.raises(OrderStateError):
        use_case.execute(CreatePaymentLinkCommand(order_id="order-1"))


def test_rejects_non_online_order_before_creating_provider_link():
    use_case = make_use_case(make_order(payment_type=PaymentMethod.CASH))

    with pytest.raises(ValueError, match="ONLINE"):
        use_case.execute(CreatePaymentLinkCommand(order_id="order-1"))


@pytest.mark.parametrize("total", [None, Decimal("0"), Decimal("-1.00")])
def test_rejects_non_positive_total_before_creating_provider_link(total):
    use_case = make_use_case(make_order(total_amount=total))

    with pytest.raises(ValueError, match="positive total"):
        use_case.execute(CreatePaymentLinkCommand(order_id="order-1"))


def test_payable_order_creates_pending_payment_and_persists_provider_link():
    payment_repo = FakePaymentRepository(reject_create=False)
    payment_provider = FakePaymentProvider(reject_create=False)
    use_case = CreatePaymentLinkUseCase(
        order_repo=FakeOrderRepository(make_order()),
        payment_repo=payment_repo,
        payment_provider=payment_provider,
    )

    result = use_case.execute(CreatePaymentLinkCommand(order_id="order-1"))

    assert result.order_id == "order-1"
    assert result.payment_id == "payment-1"
    assert result.provider == "MERCADOPAGO"
    assert result.checkout_url == "https://pay.example/checkout"
    assert result.status == "PENDING"
    assert len(payment_repo.created) == 1
    assert len(payment_provider.requests) == 1
    assert payment_provider.requests[0].currency == "ARS"
    assert payment_provider.requests[0].amount == Decimal("1500.00")
    assert payment_provider.requests[0].external_reference == "order-1"
    assert len(payment_repo.saved) == 1
    saved_payment = payment_repo.saved[0]
    assert saved_payment.preference_id == "pref-1"
    assert saved_payment.checkout_url == "https://pay.example/checkout"
    assert saved_payment.external_id == "external-1"
