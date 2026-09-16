import pytest
from decimal import Decimal
from unittest.mock import Mock

from modules.order.application.use_cases.remove_line_use_case import RemoveLineUseCase
from modules.order.application.ports.driver.remove_line_port import RemoveLineCommand
from modules.order.domain.models.order import Order
from modules.order.domain.models.order_state import OrderState
from modules.order.domain.models.order_line import OrderLine
from modules.order.domain.errors.order_errors import OrderNotFound, InvalidLineError

def test_remove_line_success():
    mock_repo = Mock()
    order = Order(id="order-1", status=OrderState.DRAFT, subtotal=Decimal("0.0"), discount=Decimal("0.0"), client_id="client-1")
    line = OrderLine("line-1", "order-1", "v-1", 1, Decimal("10.0"), Decimal("10.0"))
    order.add_line(line)
    mock_repo.get_by_id.return_value = order

    use_case = RemoveLineUseCase(order_repo=mock_repo)
    command = RemoveLineCommand(order_id="order-1", line_id="line-1")

    response = use_case.remove_line(command)

    assert response.order_id == "order-1"
    assert response.line_count == 0
    assert response.total_amount == "0.0"

    mock_repo.save.assert_called_once_with(order)
