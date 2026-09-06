from decimal import Decimal

from modules.order.application.ports.driver.update_line_quantity_port import (
    UpdateLineQuantityPort,
    UpdateLineQuantityCommand,
    UpdateLineQuantityResponse,
)
from modules.order.application.ports.driven.order_repository import OrderRepository
from modules.order.application.ports.driven.catalog_query import CatalogQuery
from modules.order.domain.errors.order_errors import OrderNotFound, InvalidLineError


class UpdateLineQuantityUseCase(UpdateLineQuantityPort):
    def __init__(self, order_repo: OrderRepository, catalog_query: CatalogQuery) -> None:
        self.order_repo = order_repo
        self.catalog_query = catalog_query

    def update_line_quantity(self, command: UpdateLineQuantityCommand) -> UpdateLineQuantityResponse:
        order = self.order_repo.get_by_id(command.order_id)
        if not order:
            raise OrderNotFound("Order not found")

        existing_line = next((l for l in order.lines if l.id == command.line_id), None)
        if not existing_line:
            raise InvalidLineError(f"Line {command.line_id} not found in order")

        # Re-fetch variant to get current price
        context = self.catalog_query.get_variant_context(existing_line.product_variant_id)
        if context is None or not context.is_sellable:
            raise InvalidLineError("Variant is no longer available")

        # Recalculate price (modifier deltas from context)
        option_lookup = {
            opt.option_id: opt
            for group in context.modifier_groups
            for opt in group.options
        }
        modifier_total = sum(
            option_lookup[m.modifier_option_id].price_delta
            for m in existing_line.modifiers
            if m.modifier_option_id in option_lookup
        )
        unit_price = context.current_price + modifier_total
        subtotal = unit_price * command.quantity

        existing_line.quantity = command.quantity
        existing_line.unit_price = unit_price
        existing_line.subtotal = subtotal
        order._recalculate_totals()

        self.order_repo.save(order)

        return UpdateLineQuantityResponse(
            order_id=order.id,
            total_amount=str(order.total_amount),
            line_count=len(order.lines),
        )
