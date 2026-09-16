"""Composition root for the delivery module.

Instantiates all driven adapters and injects them into every use case.
The shared Prisma lazy singleton is the single data-layer connection.
The OPENROUTESERVICE_API_KEY is read from Django settings (populated from env).
"""

from __future__ import annotations

from functools import lru_cache

from django.conf import settings

from modules.delivery.application.use_cases.calculate_delivery_quote_use_case import (
    CalculateDeliveryQuoteUseCase,
)
from modules.delivery.application.use_cases.configure_delivery_use_case import (
    ConfigureDeliveryUseCase,
)
from modules.delivery.application.use_cases.get_delivery_configuration_use_case import (
    GetDeliveryConfigurationUseCase,
)
from modules.delivery.domain.services.delivery_price_calculator import (
    DeliveryPriceCalculator,
)
from modules.delivery.infrastructure.adapters.driven.clock.system_clock import (
    SystemClock,
)
from modules.delivery.infrastructure.adapters.driven.geocoding.ors_geocoding_adapter import (
    OpenRouteServiceGeocodingAdapter,
)
from modules.delivery.infrastructure.adapters.driven.geometry.shapely_delivery_zone_adapter import (
    ShapelyDeliveryZoneAdapter,
)
from modules.delivery.infrastructure.adapters.driven.prisma.business_address_query import (
    BusinessAddressQuery,
)
from modules.delivery.infrastructure.adapters.driven.prisma.delivery_configuration_repository import (
    DeliveryConfigurationRepository,
)
from modules.delivery.infrastructure.adapters.driven.prisma.order_demand_adapter import (
    OrderDemandAdapter,
)
from modules.delivery.infrastructure.adapters.driven.routing.ors_routing_adapter import (
    OpenRouteServiceRoutingAdapter,
)
from shared.infrastructure.prisma.db import db


class DeliveryContainer:
    """Wires all delivery adapters into the use cases."""

    def __init__(self) -> None:
        api_key: str = getattr(settings, "OPENROUTESERVICE_API_KEY", "")

        # Driven adapters
        delivery_config_repo = DeliveryConfigurationRepository(db.client)
        address_query = BusinessAddressQuery(db.client)
        demand_adapter = OrderDemandAdapter(db.client)
        geometry = ShapelyDeliveryZoneAdapter()
        geocoding = OpenRouteServiceGeocodingAdapter(api_key=api_key)
        routing = OpenRouteServiceRoutingAdapter(api_key=api_key)
        clock = SystemClock()
        price_calculator = DeliveryPriceCalculator()

        # Use cases
        self.configure_delivery = ConfigureDeliveryUseCase(
            delivery_config_repo=delivery_config_repo,
            address_query=address_query,
            geometry=geometry,
        )
        self.get_delivery_configuration = GetDeliveryConfigurationUseCase(
            delivery_config_repo=delivery_config_repo,
        )
        self.calculate_delivery_quote = CalculateDeliveryQuoteUseCase(
            delivery_config_repo=delivery_config_repo,
            geocoding=geocoding,
            geometry=geometry,
            routing=routing,
            demand_provider=demand_adapter,
            clock=clock,
            price_calculator=price_calculator,
        )


@lru_cache(maxsize=1)
def get_delivery_container() -> DeliveryContainer:
    """Return the module's singleton composition root."""
    return DeliveryContainer()
