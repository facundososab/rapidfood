import pytest
from decimal import Decimal
from modules.order.domain.models.order import Order
from modules.order.domain.models.order_line import OrderLine
from modules.order.domain.models.order_state import OrderState
from modules.order.domain.errors.order_errors import OrderStateError, InvalidLineError

def test_new_order_is_empty_and_draft():
    order = Order(
        id="123",
        status=OrderState.DRAFT,
        subtotal=Decimal("0.0"),
        discount=Decimal("0.0"),
        client_id="client-1"
    )
    assert order.status == OrderState.DRAFT
    assert len(order.lines) == 0
    assert order.total_amount is None

def test_add_line_calculates_total():
    order = Order(id="123", status=OrderState.DRAFT, subtotal=Decimal("0.0"), discount=Decimal("0.0"), client_id="client-1")
    line = OrderLine(
        id="line-1",
        order_id="123",
        product_id="prod-1",
        quantity=2,
        unit_price=Decimal("10.5"),
        subtotal=Decimal("21.0")
    )
    
    order.add_line(line)
    
    assert len(order.lines) == 1
    assert order.total_amount == Decimal("21.0")

def test_add_line_updates_existing_product():
    order = Order(id="123", status=OrderState.DRAFT, subtotal=Decimal("0.0"), discount=Decimal("0.0"), client_id="client-1")
    line1 = OrderLine(
        id="line-1", order_id="123", product_id="prod-1",
        quantity=2, unit_price=Decimal("10.0"), subtotal=Decimal("20.0")
    )
    order.add_line(line1)
    
    line2 = OrderLine(
        id="line-1", order_id="123", product_id="prod-1",
        quantity=3, unit_price=Decimal("10.0"), subtotal=Decimal("30.0")
    )
    order.add_line(line2)
    
    assert len(order.lines) == 1
    assert order.lines[0].quantity == 3
    assert order.total_amount == Decimal("30.0")

def test_remove_line_updates_total():
    order = Order(id="123", status=OrderState.DRAFT, subtotal=Decimal("0.0"), discount=Decimal("0.0"), client_id="client-1")
    line1 = OrderLine(
        id="line-1", order_id="123", product_id="prod-1",
        quantity=2, unit_price=Decimal("10.0"), subtotal=Decimal("20.0")
    )
    order.add_line(line1)
    
    order.remove_line("prod-1")
    
    assert len(order.lines) == 0
    assert order.total_amount == Decimal("0.0")

def test_cannot_modify_lines_if_not_draft():
    order = Order(id="123", status=OrderState.DRAFT, subtotal=Decimal("0.0"), discount=Decimal("0.0"), client_id="client-1")
    order.status = OrderState.CONFIRMED
    
    line = OrderLine(
        id="line-1", order_id="123", product_id="prod-1",
        quantity=2, unit_price=Decimal("10.0"), subtotal=Decimal("20.0")
    )
    
    with pytest.raises(OrderStateError):
        order.add_line(line)
        
    with pytest.raises(OrderStateError):
        order.remove_line("prod-1")
