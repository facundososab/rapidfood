from datetime import datetime
from modules.order.application.ports.driver.confirm_order_ports import (
    ConfirmOrderPort, ConfirmOrderCommand, ConfirmOrderResponse
)
from modules.order.application.ports.driven.order_repository import OrderRepository
from modules.order.application.ports.driven.business_config_query import BusinessConfigQueryPort
from modules.order.application.ports.driven.catalog_query import CatalogQuery
from modules.order.domain.errors.order_errors import (
    OrderNotFound, OrderNotModifiableError, BusinessClosedError, 
    MinimumOrderNotMetError, InvalidLineError
)
from modules.order.domain.models.order_state import OrderState


class ConfirmOrderUseCase(ConfirmOrderPort):
    def __init__(self, order_repo: OrderRepository, config_query: BusinessConfigQueryPort, catalog_query: CatalogQuery):
        self.order_repo = order_repo
        self.config_query = config_query
        self.catalog_query = catalog_query

    def execute(self, command: ConfirmOrderCommand) -> ConfirmOrderResponse:
        order = self.order_repo.get_by_id(command.order_id)
        if not order:
            raise OrderNotFound("Order not found")

        if order.status != OrderState.DRAFT:
            raise OrderNotModifiableError("Only DRAFT orders can be confirmed")

        if not order.lines:
            raise InvalidLineError("Cannot confirm an empty order")

        # 1. Check if business is open
        config = self.config_query.get_config()
        if not config.is_open:
            raise BusinessClosedError("Business is currently closed")

        # 2. Check minimum order amount
        if order.subtotal < config.min_order_amount:
            raise MinimumOrderNotMetError(f"Minimum order amount is {config.min_order_amount}")

        # 3. Validate lines against current catalog
        for line in order.lines:
            product = self.catalog_query.get_product(line.product_id)
            if not product or not product.is_available:
                raise InvalidLineError(f"Product {line.product_id} is no longer available")
            
            # Update prices to the very latest right before confirming
            line.unit_price = product.price
            line.subtotal = line.quantity * product.price

        # 4. Advance state
        order._recalculate_totals()
        order.status = OrderState.PENDING
        
        self.order_repo.save(order)

        return ConfirmOrderResponse(
            order_id=order.id,
            status=order.status.value,
            confirmed_at=datetime.utcnow().isoformat()
        )
