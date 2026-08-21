"""CalculateDeliveryQuoteUseCase.

Main use case for delivery quote calculation. Orchestrates:
    1. Load delivery configuration
    2. Verify configuration is complete
    3. Geocode destination address
    4. Check if destination is inside the delivery zone
    5. If outside -> return DeliveryQuote(available=False) immediately
    6. Geocode origin address (only after zone check passes)
    7. Calculate street-distance route
    8. Determine demand window start time
    9. Count active delivery orders for this restaurant
   10. Classify demand level and get multiplier
   11. Determine weekday and get weekday multiplier
   12. Calculate shipping cost via DeliveryPriceCalculator
   13. Return DeliveryQuote

IMPORTANT: Routing is called ONLY after the zone check passes.
           A provider failure (geocoding/routing) raises an error —
           it is NOT treated as "delivery unavailable".
"""

from __future__ import annotations

from datetime import timedelta

from modules.delivery.application.ports.driven.clock_port import ClockPort
from modules.delivery.application.ports.driven.delivery_configuration_repository_port import (
    DeliveryConfigurationRepositoryPort,
)
from modules.delivery.application.ports.driven.delivery_zone_geometry_port import (
    DeliveryZoneGeometryPort,
)
from modules.delivery.application.ports.driven.geocoding_provider_port import (
    GeocodingProviderPort,
)
from modules.delivery.application.ports.driven.order_demand_provider_port import (
    OrderDemandProviderPort,
)
from modules.delivery.application.ports.driven.routing_provider_port import (
    RoutingProviderPort,
)
from modules.delivery.application.ports.driver.calculate_delivery_quote_ports import (
    CalculateDeliveryQuoteCommand,
    CalculateDeliveryQuotePort,
    CalculateDeliveryQuoteResponse,
)
from modules.delivery.domain.errors.delivery_errors import (
    BusinessConfigurationNotFoundError,
    DeliveryConfigurationNotFoundError,
    DeliveryOriginNotConfiguredError,
    DeliveryZoneNotConfiguredError,
)
from modules.delivery.domain.models.postal_address import PostalAddress
from modules.delivery.domain.models.week_day import WeekDay
from modules.delivery.domain.services.demand_classifier import classify_demand
from modules.delivery.domain.services.delivery_price_calculator import (
    DeliveryPriceCalculator,
)

_WEEKDAY_MAP = {
    0: WeekDay.MONDAY,
    1: WeekDay.TUESDAY,
    2: WeekDay.WEDNESDAY,
    3: WeekDay.THURSDAY,
    4: WeekDay.FRIDAY,
    5: WeekDay.SATURDAY,
    6: WeekDay.SUNDAY,
}


class CalculateDeliveryQuoteUseCase(CalculateDeliveryQuotePort):
    """Calculates a real-time delivery quote for a customer's destination."""

    def __init__(
        self,
        delivery_config_repo: DeliveryConfigurationRepositoryPort,
        geocoding: GeocodingProviderPort,
        geometry: DeliveryZoneGeometryPort,
        routing: RoutingProviderPort,
        demand_provider: OrderDemandProviderPort,
        clock: ClockPort,
        price_calculator: DeliveryPriceCalculator,
    ) -> None:
        self._repo = delivery_config_repo
        self._geocoding = geocoding
        self._geometry = geometry
        self._routing = routing
        self._demand_provider = demand_provider
        self._clock = clock
        self._calculator = price_calculator

    def execute(
        self, command: CalculateDeliveryQuoteCommand
    ) -> CalculateDeliveryQuoteResponse:
        # Step 1: Load configuration
        config = self._repo.get_by_business_config_id(command.business_config_id)
        if config is None:
            raise BusinessConfigurationNotFoundError(
                f"Business configuration {command.business_config_id} not found."
            )

        # Step 2: Verify configuration is complete
        if not config.is_fully_configured:
            raise DeliveryConfigurationNotFoundError(
                f"Delivery has not been fully configured for "
                f"business {command.business_config_id}."
            )

        delivery_zone = config.delivery_zone
        pricing_config = config.pricing_config

        # Step 3: Geocode destination
        dest_address = PostalAddress(
            street=command.destination_address.street,
            street_number=command.destination_address.street_number,
            city=command.destination_address.city,
            province=command.destination_address.province,
            floor=command.destination_address.floor,
            apartment=command.destination_address.apartment,
            postal_code=command.destination_address.postal_code,
        )
        # Raises AddressCouldNotBeGeocodedError or GeocodingProviderError on failure
        destination_coords = self._geocoding.geocode(dest_address)

        # Step 4: Check if destination is inside the zone
        is_inside = self._geometry.covers(delivery_zone, destination_coords)

        # Step 5: Outside zone — return immediately without routing
        if not is_inside:
            return CalculateDeliveryQuoteResponse(available=False)

        # Step 6: Geocode origin address
        origin_coords = self._geocoding.geocode(config.origin_address)

        # Step 7: Calculate street-distance route (raises RoutingProviderError on failure)
        route = self._routing.calculate_route(
            origin=origin_coords,
            destination=destination_coords,
        )

        # Step 8: Determine demand window
        now = self._clock.utc_now()
        window_start = now - timedelta(minutes=pricing_config.demand_window_minutes)

        # Step 9: Count active delivery orders for this restaurant
        active_orders = self._demand_provider.count_recent_active_delivery_orders(
            business_config_id=command.business_config_id,
            since=window_start,
        )

        # Step 10: Classify demand and get multiplier
        demand_level, demand_multiplier = classify_demand(active_orders, pricing_config)

        # Step 11: Determine current weekday and get multiplier
        current_weekday = _WEEKDAY_MAP[now.weekday()]
        weekday_multiplier = pricing_config.weekday_multipliers[current_weekday]

        # Step 12: Calculate shipping cost
        shipping_cost = self._calculator.calculate(
            base_shipping_cost=config.base_shipping_cost,
            distance_km=route.distance_km,
            price_per_km=pricing_config.price_per_km,
            weekday_multiplier=weekday_multiplier,
            demand_multiplier=demand_multiplier,
        )

        # Step 13: Return quote
        return CalculateDeliveryQuoteResponse(
            available=True,
            distance_km=route.distance_km,
            estimated_duration_minutes=route.duration_minutes,
            shipping_cost=shipping_cost,
            demand_level=demand_level.value,
        )
