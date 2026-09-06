import pytest
from decimal import Decimal
from modules.order.domain.models.order import Order
from modules.order.domain.models.order_line import OrderLine
from modules.order.domain.models.order_line_modifier import OrderLineModifier
from modules.order.domain.models.order_state import OrderState


def make_order():
    return Order(
        id="order-1",
        status=OrderState.DRAFT,
        subtotal=Decimal("0"),
        discount=Decimal("0"),
    )


def make_line(line_id="line-1", variant_id="v-1", qty=1, unit_price=Decimal("100"), modifiers=None):
    subtotal = unit_price * qty
    return OrderLine(
        id=line_id,
        order_id="order-1",
        product_variant_id=variant_id,
        quantity=qty,
        unit_price=unit_price,
        subtotal=subtotal,
        modifiers=modifiers or [],
    )


def test_single_line_no_modifiers():
    order = make_order()
    line = make_line(unit_price=Decimal("100"), qty=2)
    order.add_line(line)
    assert order.total_amount == Decimal("200")


def test_two_lines_same_variant_different_ids():
    """Multiple lines with the same variant are allowed if they have different IDs."""
    order = make_order()
    line1 = make_line(line_id="line-1", variant_id="v-1", unit_price=Decimal("100"), qty=1)
    line2 = make_line(line_id="line-2", variant_id="v-1", unit_price=Decimal("200"), qty=1)
    order.add_line(line1)
    order.add_line(line2)
    assert len(order.lines) == 2
    assert order.total_amount == Decimal("300")


def test_unit_price_with_modifiers():
    """Modifiers are summed into unit_price before creating the line."""
    # 10500 base + 1000 bacon + 500 extra cheese = 12000
    unit_price = Decimal("10500") + Decimal("1000") + Decimal("500")
    line = make_line(unit_price=unit_price, qty=2)
    assert line.subtotal == Decimal("24000")


def test_remove_line_by_id():
    order = make_order()
    line = make_line(line_id="line-1")
    order.add_line(line)
    order.remove_line("line-1")
    assert len(order.lines) == 0
    assert order.total_amount == Decimal("0")


def test_removed_ingredients_do_not_affect_price():
    """Removing ingredients does not change unit_price or subtotal."""
    from modules.order.domain.models.order_line_removed_ingredient import OrderLineRemovedIngredient
    removed = OrderLineRemovedIngredient(
        id="r-1",
        order_line_id="line-1",
        ingredient_id="ing-1",
        ingredient_name_snapshot="Lechuga",
    )
    line = OrderLine(
        id="line-1",
        order_id="order-1",
        product_variant_id="v-1",
        quantity=1,
        unit_price=Decimal("100"),
        subtotal=Decimal("100"),
        removed_ingredients=[removed],
    )
    assert line.subtotal == Decimal("100")
    assert line.unit_price == Decimal("100")
