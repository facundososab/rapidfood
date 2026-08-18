from modules.order.application.ports.driver.update_line_quantity_port import (
    UpdateLineQuantityPort, UpdateLineQuantityCommand, UpdateLineQuantityResponse
)
from modules.order.application.ports.driven.order_repository import OrderRepository
from modules.order.application.ports.driven.catalog_query import CatalogQuery
from modules.order.domain.models.order_line import OrderLine
from modules.order.domain.errors.order_errors import OrderNotFound, InvalidLineError


class UpdateLineQuantityUseCase(UpdateLineQuantityPort):
    def __init__(self, order_repo: OrderRepository, catalog_query: CatalogQuery):
        self.order_repo = order_repo
        self.catalog_query = catalog_query

    def update_line_quantity(self, command: UpdateLineQuantityCommand) -> UpdateLineQuantityResponse:
        order = self.order_repo.get_by_id(command.order_id)
        if not order:
            raise OrderNotFound("Order not found")

        # Get existing line to find product price
        existing_line = next((l for l in order.lines if l.product_id == command.product_id), None)
        if not existing_line:
            raise InvalidLineError("Line not found in order")

        # Re-fetch product to ensure it's still available and get latest price
        product = self.catalog_query.get_product(command.product_id)
        if not product or not product.is_available:
            raise InvalidLineError("Product no longer available")

        new_line = OrderLine(
            id=existing_line.id,
            order_id=order.id,
            product_id=product.product_id,
            quantity=command.quantity,
            unit_price=product.price,
            subtotal=product.price * command.quantity
        )
        
        order.add_line(new_line) # add_line acts as an upsert based on product_id
        self.order_repo.save(order)
        
        return UpdateLineQuantityResponse(
            order_id=order.id,
            total_amount=str(order.total_amount),
            line_count=len(order.lines)
        )
