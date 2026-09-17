from decimal import Decimal
from typing import Optional

from modules.order.application.ports.driver.configure_order_ports import (
    ConfigureOrderPort, SetDeliveryDetailsCommand, SetDeliveryDetailsResponse
)
from modules.order.application.ports.driven.order_repository import OrderRepository
from modules.order.application.ports.driven.business_config_query import BusinessConfigQueryPort
from modules.order.application.ports.driven.delivery_quote_query import DeliveryQuoteQuery
from modules.order.domain.errors.order_errors import (
    OrderNotFound,
    OrderNotModifiableError,
    DeliveryNotAvailableError,
    DeliveryAddressRequiredError,
)
from modules.order.domain.models.delivery_address import DeliveryAddress
from modules.order.domain.models.delivery_type import DeliveryType
from modules.order.domain.models.order_state import OrderState


class ConfigureOrderUseCase(ConfigureOrderPort):
    def __init__(
        self,
        order_repo: OrderRepository,
        config_query: BusinessConfigQueryPort,
        delivery_quote: Optional[DeliveryQuoteQuery] = None,
    ):
        self.order_repo = order_repo
        self.config_query = config_query
        self.delivery_quote = delivery_quote

    def set_delivery_details(self, command: SetDeliveryDetailsCommand) -> SetDeliveryDetailsResponse:
        order = self.order_repo.get_by_id(command.order_id)
        if not order:
            raise OrderNotFound("Order not found")

        if order.status != OrderState.DRAFT:
            raise OrderNotModifiableError("Cannot configure an order that is not in DRAFT state")

        delivery_type = DeliveryType(command.delivery_type)
        order.delivery_type = delivery_type

        if delivery_type == DeliveryType.DELIVERY:
            destination = _destination_from(command)
            config = self.config_query.get_config()
            order.business_config_id = config.business_config_id
            order.address_id = command.address_id
            order.delivery_address = destination
            order.shipping_cost = self._quote_shipping(config, destination)
        else:
            order.address_id = None
            order.delivery_address = None
            order.shipping_cost = Decimal("0")

        # Recalculate totals with new shipping cost
        order._recalculate_totals()

        self.order_repo.save(order)

        return SetDeliveryDetailsResponse(
            order_id=order.id,
            shipping_cost=str(order.shipping_cost),
            total_amount=str(order.total_amount)
        )

    def _quote_shipping(self, config, destination: DeliveryAddress) -> Decimal:
        """Real quote when a delivery provider is wired; flat config cost otherwise."""
        if self.delivery_quote is None:
            return config.shipping_cost

        quote = self.delivery_quote.quote(config.business_config_id, destination)
        if not quote.available or quote.shipping_cost is None:
            raise DeliveryNotAvailableError(
                "No se puede entregar en esa dirección."
            )
        return quote.shipping_cost


def _destination_from(command: SetDeliveryDetailsCommand) -> DeliveryAddress:
    street = (command.street or "").strip()
    street_number = (command.street_number or "").strip()
    city = (command.city or "").strip()
    province = (command.province or "").strip()
    if not (street and street_number and city and province):
        raise DeliveryAddressRequiredError(
            "Completá calle, número, ciudad y provincia para el envío."
        )
    return DeliveryAddress(
        street=street,
        street_number=street_number,
        city=city,
        province=province,
        floor=(command.floor or "").strip() or None,
        apartment=(command.apartment or "").strip() or None,
        postal_code=(command.postal_code or "").strip() or None,
    )
