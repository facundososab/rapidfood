import uuid

from modules.order.application.ports.driver.add_line_port import (
    AddLinePort, AddLineCommand, AddLineResponse
)
from modules.order.application.ports.driven.order_repository import OrderRepository
from modules.order.application.ports.driven.catalog_query import CatalogQuery
from modules.order.domain.models.order_line import OrderLine
from modules.order.domain.errors.order_errors import OrderNotFound, InvalidLineError


class AddLineUseCase(AddLinePort):
    def __init__(self, order_repo: OrderRepository, catalog_query: CatalogQuery):
        self.order_repo = order_repo
        self.catalog_query = catalog_query

    def add_line(self, command: AddLineCommand) -> AddLineResponse:
        order = self.order_repo.get_by_id(command.order_id)
        if not order:
            raise OrderNotFound("Order not found")

        product = self.catalog_query.get_product(command.product_id)
        if not product or not product.is_available:
            raise InvalidLineError("Product not available")

        line = OrderLine(
            id=str(uuid.uuid4()),
            order_id=order.id,
            product_id=product.product_id,
            quantity=command.quantity,
            unit_price=product.price,
            subtotal=product.price * command.quantity
        )
        
        order.add_line(line)
        self.order_repo.save(order)
        
        return AddLineResponse(
            order_id=order.id,
            total_amount=str(order.total_amount),
            line_count=len(order.lines)
        )
