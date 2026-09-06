import pytest
from decimal import Decimal
from modules.order.domain.models.order import Order
from modules.order.domain.models.order_line import OrderLine
from modules.order.domain.models.order_state import OrderState
from modules.order.domain.errors.order_errors import OrderStateError, InvalidLineError


def _make_line(line_id, variant_id, qty, unit_price, subtotal):
    return OrderLine(
        id=line_id,
        order_id="123",
        product_variant_id=variant_id,
        quantity=qty,
        unit_price=unit_price,
        subtotal=subtotal,
    )


def test_new_order_is_empty_and_draft():
    order = Order(
        id="123",
        status=OrderState.DRAFT,
        subtotal=Decimal("0.0"),
        discount=Decimal("0.0"),
        client_id="client-1",
    )
    assert order.status == OrderState.DRAFT
    assert len(order.lines) == 0
    assert order.total_amount is None


def test_add_line_calculates_total():
    order = Order(
        id="123", status=OrderState.DRAFT,
        subtotal=Decimal("0.0"), discount=Decimal("0.0"), client_id="client-1",
    )
    line = _make_line("line-1", "v-1", 2, Decimal("10.5"), Decimal("21.0"))
    order.add_line(line)
    assert len(order.lines) == 1
    assert order.total_amount == Decimal("21.0")


def test_add_line_updates_existing_line_by_id():
    """Adding a line with the same id as an existing one updates it in-place."""
    order = Order(
        id="123", status=OrderState.DRAFT,
        subtotal=Decimal("0.0"), discount=Decimal("0.0"), client_id="client-1",
    )
    line1 = _make_line("line-1", "v-1", 2, Decimal("10.0"), Decimal("20.0"))
    order.add_line(line1)

    # Same id, same variant, different quantity
    line2 = _make_line("line-1", "v-1", 3, Decimal("10.0"), Decimal("30.0"))
    order.add_line(line2)

    assert len(order.lines) == 1
    assert order.lines[0].quantity == 3
    assert order.total_amount == Decimal("30.0")


def test_two_lines_same_variant_allowed():
    """Different line ids with the same variant should coexist."""
    order = Order(
        id="123", status=OrderState.DRAFT,
        subtotal=Decimal("0.0"), discount=Decimal("0.0"), client_id="client-1",
    )
    line1 = _make_line("line-1", "v-1", 1, Decimal("10.0"), Decimal("10.0"))
    line2 = _make_line("line-2", "v-1", 1, Decimal("20.0"), Decimal("20.0"))
    order.add_line(line1)
    order.add_line(line2)
    assert len(order.lines) == 2
    assert order.total_amount == Decimal("30.0")


def test_remove_line_by_line_id():
    order = Order(
        id="123", status=OrderState.DRAFT,
        subtotal=Decimal("0.0"), discount=Decimal("0.0"), client_id="client-1",
    )
    line = _make_line("line-1", "v-1", 2, Decimal("10.0"), Decimal("20.0"))
    order.add_line(line)
    order.remove_line("line-1")
    assert len(order.lines) == 0
    assert order.total_amount == Decimal("0.0")


def test_cannot_modify_lines_if_not_draft():
    order = Order(
        id="123", status=OrderState.DRAFT,
        subtotal=Decimal("0.0"), discount=Decimal("0.0"), client_id="client-1",
    )
    order.status = OrderState.CONFIRMED

    line = _make_line("line-1", "v-1", 2, Decimal("10.0"), Decimal("20.0"))

    with pytest.raises(OrderStateError):
        order.add_line(line)

    with pytest.raises(OrderStateError):
        order.remove_line("line-1")


