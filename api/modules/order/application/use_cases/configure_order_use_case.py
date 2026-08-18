from modules.order.application.ports.driver.configure_order_ports import (
    ConfigureOrderPort, SetDeliveryDetailsCommand, SetDeliveryDetailsResponse
)
from modules.order.application.ports.driven.order_repository import OrderRepository
from modules.order.application.ports.driven.business_config_query import BusinessConfigQueryPort
from modules.order.domain.errors.order_errors import OrderNotFound, OrderNotModifiableError
from modules.order.domain.models.delivery_type import DeliveryType
from modules.order.domain.models.order_state import OrderState


class ConfigureOrderUseCase(ConfigureOrderPort):
    def __init__(self, order_repo: OrderRepository, config_query: BusinessConfigQueryPort):
        self.order_repo = order_repo
        self.config_query = config_query

    def set_delivery_details(self, command: SetDeliveryDetailsCommand) -> SetDeliveryDetailsResponse:
        order = self.order_repo.get_by_id(command.order_id)
        if not order:
            raise OrderNotFound("Order not found")

        if order.status != OrderState.DRAFT:
            raise OrderNotModifiableError("Cannot configure an order that is not in DRAFT state")

        delivery_type = DeliveryType(command.delivery_type)
        order.delivery_type = delivery_type

        if delivery_type == DeliveryType.DELIVERY:
            order.address_id = command.address_id
            config = self.config_query.get_config()
            order.shipping_cost = config.shipping_cost
        else:
            order.address_id = None
            order.shipping_cost = 0

        # Recalculate totals with new shipping cost
        order._recalculate_totals()
        
        self.order_repo.save(order)

        return SetDeliveryDetailsResponse(
            order_id=order.id,
            shipping_cost=str(order.shipping_cost),
            total_amount=str(order.total_amount)
        )
