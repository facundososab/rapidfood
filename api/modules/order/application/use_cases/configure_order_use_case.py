from decimal import Decimal
from typing import Optional

from modules.order.application.ports.driver.configure_order_ports import (
    ConfigureOrderPort, SetDeliveryDetailsCommand, SetDeliveryDetailsResponse
)
from modules.order.application.ports.driven.order_repository import OrderRepository
from modules.order.application.ports.driven.business_config_query import BusinessConfigQueryPort
from modules.order.application.ports.driven.delivery_quote_query import (
    DeliveryQuoteQuery,
    DeliveryQuoteSnapshot,
)
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
        prep_time_estimator: Optional[object] = None,
    ):
        self.order_repo = order_repo
        self.config_query = config_query
        self.delivery_quote = delivery_quote
        self.prep_time_estimator = prep_time_estimator

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
            quote = self._quote(config, destination)
            order.shipping_cost = quote.shipping_cost
            order.route_duration_minutes = (
                round(quote.estimated_duration_minutes)
                if quote.estimated_duration_minutes is not None
                else None
            )
        else:
            order.address_id = None
            order.delivery_address = None
            order.shipping_cost = Decimal("0")
            order.route_duration_minutes = None

        order.estimated_time = self._estimate_time(order)

        # Recalculate totals with new shipping cost
        order._recalculate_totals()

        self.order_repo.save(order)

        return SetDeliveryDetailsResponse(
            order_id=order.id,
            shipping_cost=str(order.shipping_cost),
            total_amount=str(order.total_amount)
        )

    def _quote(
        self, config, destination: DeliveryAddress
    ) -> DeliveryQuoteSnapshot:
        """Real quote when a delivery provider is wired; flat config cost otherwise."""
        if self.delivery_quote is None:
            return DeliveryQuoteSnapshot(
                available=True, shipping_cost=config.shipping_cost
            )

        quote = self.delivery_quote.quote(config.business_config_id, destination)
        if not quote.available or quote.shipping_cost is None:
            raise DeliveryNotAvailableError(
                "No se puede entregar en esa dirección."
            )
        return quote

    def _estimate_time(self, order) -> Optional[int]:
        """ETA = preparation (demand) + delivery travel time, when available."""
        if self.prep_time_estimator is None or not order.business_config_id:
            return order.estimated_time
        prep = self.prep_time_estimator.estimate_minutes(order.business_config_id)
        return prep + (order.route_duration_minutes or 0)


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
