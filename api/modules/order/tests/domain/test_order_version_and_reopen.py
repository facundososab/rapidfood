"""Order versioning and explicit reopen for online orders awaiting payment."""
from decimal import Decimal

import pytest

from modules.order.domain.errors.order_errors import OrderStateError
from modules.order.domain.models.delivery_type import DeliveryType
from modules.order.domain.models.order import Order
from modules.order.domain.models.order_line import OrderLine
from modules.order.domain.models.order_state import OrderState
from modules.order.domain.models.payment_method import PaymentMethod


def make_order(status=OrderState.DRAFT, payment_type=None, version=0):
    order = Order(
        id="o-1",
        status=status,
        subtotal=Decimal("0"),
        discount=Decimal("0"),
        payment_type=payment_type,
        version=version,
    )
    return order


def make_line(line_id="line-1", variant_id="v-1", subtotal=Decimal("100")):
    return OrderLine(
        id=line_id,
        order_id="o-1",
        product_variant_id=variant_id,
        quantity=1,
        unit_price=subtotal,
        subtotal=subtotal,
    )


def test_new_order_starts_at_version_zero():
    assert make_order().version == 0


def test_add_line_increments_version():
    order = make_order()
    order.add_line(make_line())
    assert order.version == 1


def test_remove_line_increments_version():
    order = make_order()
    order.add_line(make_line())
    order.remove_line("line-1")
    assert order.version == 2


def test_set_delivery_details_increments_version():
    order = make_order()
    order.set_delivery_details(DeliveryType.PICKUP)
    assert order.version == 1


def test_reopen_pending_online_without_approved_payment():
    order = make_order(status=OrderState.PENDING, payment_type=PaymentMethod.ONLINE)
    order.confirmed_at = "some-timestamp"

    order.reopen_for_modification(has_current_approved_payment=False)

    assert order.status is OrderState.DRAFT
    assert order.confirmed_at is None


def test_reopen_rejected_when_not_pending():
    with pytest.raises(OrderStateError):
        make_order(status=OrderState.DRAFT, payment_type=PaymentMethod.ONLINE).reopen_for_modification()


def test_reopen_rejected_when_paid():
    with pytest.raises(OrderStateError):
        make_order(status=OrderState.PAID, payment_type=PaymentMethod.ONLINE).reopen_for_modification()


def test_reopen_rejected_for_cash():
    with pytest.raises(OrderStateError):
        make_order(status=OrderState.PENDING, payment_type=PaymentMethod.CASH).reopen_for_modification()


def test_reopen_rejected_when_current_payment_approved():
    order = make_order(status=OrderState.PENDING, payment_type=PaymentMethod.ONLINE)
    with pytest.raises(OrderStateError):
        order.reopen_for_modification(has_current_approved_payment=True)
    assert order.status is OrderState.PENDING
