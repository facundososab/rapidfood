import pytest
from decimal import Decimal
from unittest.mock import Mock

from modules.order.application.use_cases.add_line_use_case import AddLineUseCase
from modules.order.application.ports.driver.add_line_port import AddLineCommand
from modules.order.domain.models.order import Order
from modules.order.domain.models.order_state import OrderState
from modules.order.domain.errors.order_errors import OrderNotFound, InvalidLineError

class MockProduct:
    def __init__(self, product_id, price, is_available):
        self.product_id = product_id
        self.price = price
        self.is_available = is_available

def test_add_line_success():
    mock_repo = Mock()
    order = Order(id="order-1", status=OrderState.DRAFT, subtotal=Decimal("0.0"), discount=Decimal("0.0"), client_id="client-1")
    mock_repo.get_by_id.return_value = order
    
    mock_catalog = Mock()
    mock_catalog.get_product.return_value = MockProduct("prod-1", Decimal("10.5"), True)
    
    use_case = AddLineUseCase(order_repo=mock_repo, catalog_query=mock_catalog)
    command = AddLineCommand(order_id="order-1", product_id="prod-1", quantity=2)
    
    response = use_case.add_line(command)
    
    assert response.order_id == "order-1"
    assert response.line_count == 1
    assert response.total_amount == "21.0"
    
    mock_repo.save.assert_called_once_with(order)

def test_add_line_fails_if_order_not_found():
    mock_repo = Mock()
    mock_repo.get_by_id.return_value = None
    mock_catalog = Mock()
    
    use_case = AddLineUseCase(order_repo=mock_repo, catalog_query=mock_catalog)
    command = AddLineCommand(order_id="order-1", product_id="prod-1", quantity=2)
    
    with pytest.raises(OrderNotFound):
        use_case.add_line(command)

def test_add_line_fails_if_product_not_available():
    mock_repo = Mock()
    order = Order(id="order-1", status=OrderState.DRAFT, subtotal=Decimal("0.0"), discount=Decimal("0.0"), client_id="client-1")
    mock_repo.get_by_id.return_value = order
    
    mock_catalog = Mock()
    mock_catalog.get_product.return_value = MockProduct("prod-1", Decimal("10.5"), False)
    
    use_case = AddLineUseCase(order_repo=mock_repo, catalog_query=mock_catalog)
    command = AddLineCommand(order_id="order-1", product_id="prod-1", quantity=2)
    
    with pytest.raises(InvalidLineError):
        use_case.add_line(command)
