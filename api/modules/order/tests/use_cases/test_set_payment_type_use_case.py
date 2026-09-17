"""Set payment type (CASH | ONLINE) use case."""
from decimal import Decimal

import pytest

from modules.order.application.ports.driver.set_payment_type_port import (
    SetPaymentTypeCommand,
)
from modules.order.application.use_cases.set_payment_type_use_case import (
    SetPaymentTypeUseCase,
)
from modules.order.domain.errors.order_errors import (
    InvalidPaymentTypeError,
    OrderNotFound,
    OrderNotModifiableError,
)
from modules.order.domain.models.order import Order
from modules.order.domain.models.order_state import OrderState
from modules.order.domain.models.payment_method import PaymentMethod


class FakeOrderRepo:
    def __init__(self, order):
        self.order = order
        self.saved = 0

    def get_by_id(self, order_id):
        return self.order

    def save(self, order):
        self.saved += 1
        return order


def _order(status=OrderState.DRAFT):
    return Order(
        id="o-1", status=status, subtotal=Decimal("0"), discount=Decimal("0")
    )


def test_sets_cash_on_a_draft():
    repo = FakeOrderRepo(_order())
    result = SetPaymentTypeUseCase(repo).execute(
        SetPaymentTypeCommand(order_id="o-1", payment_type="CASH")
    )
    assert result.payment_type == "CASH"
    assert repo.order.payment_type is PaymentMethod.CASH
    assert repo.saved == 1


def test_sets_online_on_a_draft():
    repo = FakeOrderRepo(_order())
    result = SetPaymentTypeUseCase(repo).execute(
        SetPaymentTypeCommand(order_id="o-1", payment_type="ONLINE")
    )
    assert result.payment_type == "ONLINE"


def test_rejects_unknown_value():
    repo = FakeOrderRepo(_order())
    with pytest.raises(InvalidPaymentTypeError):
        SetPaymentTypeUseCase(repo).execute(
            SetPaymentTypeCommand(order_id="o-1", payment_type="CARD")
        )


def test_rejects_non_draft_order():
    repo = FakeOrderRepo(_order(status=OrderState.PENDING))
    with pytest.raises(OrderNotModifiableError):
        SetPaymentTypeUseCase(repo).execute(
            SetPaymentTypeCommand(order_id="o-1", payment_type="CASH")
        )


def test_rejects_missing_order():
    class _Empty:
        def get_by_id(self, order_id):
            return None

        def save(self, order):
            return order

    with pytest.raises(OrderNotFound):
        SetPaymentTypeUseCase(_Empty()).execute(
            SetPaymentTypeCommand(order_id="missing", payment_type="CASH")
        )
