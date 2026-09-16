import pytest
from decimal import Decimal
from unittest.mock import Mock

from modules.order.application.use_cases.update_line_quantity_use_case import UpdateLineQuantityUseCase
from modules.order.application.ports.driver.update_line_quantity_port import UpdateLineQuantityCommand
from modules.order.application.ports.driven.catalog_query import VariantContext
from modules.order.domain.models.order import Order
from modules.order.domain.models.order_state import OrderState
from modules.order.domain.models.order_line import OrderLine
from modules.order.domain.errors.order_errors import OrderNotFound, InvalidLineError


def _make_variant_context(variant_id="v-1", price=Decimal("10.0"), sellable=True):
    return VariantContext(
        product_id="p-1",
        product_name="Pizza",
        product_available=sellable,
        variant_id=variant_id,
        variant_name="Regular",
        variant_available=sellable,
        current_price=price,
    )


def test_update_line_quantity_success():
    mock_repo = Mock()
    order = Order(id="order-1", status=OrderState.DRAFT, subtotal=Decimal("0.0"), discount=Decimal("0.0"), client_id="client-1")
    line = OrderLine("line-1", "order-1", "v-1", 1, Decimal("10.0"), Decimal("10.0"))
    order.add_line(line)
    mock_repo.get_by_id.return_value = order

    mock_catalog = Mock()
    mock_catalog.get_variant_context.return_value = _make_variant_context(
        variant_id="v-1", price=Decimal("10.0"), sellable=True
    )

    use_case = UpdateLineQuantityUseCase(order_repo=mock_repo, catalog_query=mock_catalog)
    command = UpdateLineQuantityCommand(order_id="order-1", line_id="line-1", quantity=3)

    response = use_case.update_line_quantity(command)

    assert response.order_id == "order-1"
    assert response.line_count == 1
    assert response.total_amount == "30.0"

    mock_repo.save.assert_called_once_with(order)


def test_update_line_quantity_fails_if_line_not_in_order():
    mock_repo = Mock()
    order = Order(id="order-1", status=OrderState.DRAFT, subtotal=Decimal("0.0"), discount=Decimal("0.0"), client_id="client-1")
    mock_repo.get_by_id.return_value = order

    mock_catalog = Mock()

    use_case = UpdateLineQuantityUseCase(order_repo=mock_repo, catalog_query=mock_catalog)
    command = UpdateLineQuantityCommand(order_id="order-1", line_id="line-not-in-order", quantity=3)

    with pytest.raises(InvalidLineError):
        use_case.update_line_quantity(command)
