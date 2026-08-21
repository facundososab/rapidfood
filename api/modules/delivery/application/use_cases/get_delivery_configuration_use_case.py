"""GetDeliveryConfigurationUseCase.

Reads the current delivery configuration for a restaurant and returns it
as a DTO suitable for the admin panel to display and pre-populate a form.
"""

from __future__ import annotations

from typing import Any, Dict, List, Optional

from modules.delivery.application.ports.driven.delivery_configuration_repository_port import (
    DeliveryConfigurationRepositoryPort,
)
from modules.delivery.application.ports.driver.get_delivery_configuration_ports import (
    GetDeliveryConfigurationPort,
    GetDeliveryConfigurationQuery,
    GetDeliveryConfigurationResponse,
    WeekdayMultiplierDto,
)
from modules.delivery.domain.errors.delivery_errors import (
    BusinessConfigurationNotFoundError,
)
from modules.delivery.domain.models.coordinates import Coordinates
from modules.delivery.domain.models.delivery_zone import DeliveryZone


def _zone_to_geojson(zone: DeliveryZone) -> Dict[str, Any]:
    """Convert domain DeliveryZone to a GeoJSON Polygon dict."""
    def ring_to_coords(ring: List[Coordinates]) -> List[List[float]]:
        return [[c.longitude, c.latitude] for c in ring]

    coordinates = [ring_to_coords(zone.exterior_ring)]
    for hole in zone.holes:
        coordinates.append(ring_to_coords(hole))

    return {"type": "Polygon", "coordinates": coordinates}


class GetDeliveryConfigurationUseCase(GetDeliveryConfigurationPort):
    """Returns the current delivery configuration for a restaurant."""

    def __init__(
        self, delivery_config_repo: DeliveryConfigurationRepositoryPort
    ) -> None:
        self._repo = delivery_config_repo

    def execute(
        self, query: GetDeliveryConfigurationQuery
    ) -> GetDeliveryConfigurationResponse:
        config = self._repo.get_by_business_config_id(query.business_config_id)

        if config is None:
            raise BusinessConfigurationNotFoundError(
                f"No business configuration found for id {query.business_config_id}."
            )

        available_zone: Optional[Dict[str, Any]] = None
        if config.delivery_zone is not None:
            available_zone = _zone_to_geojson(config.delivery_zone)

        weekday_multipliers: List[WeekdayMultiplierDto] = []
        price_per_km = None
        demand_window_minutes = None
        high_demand_threshold = None
        very_high_demand_threshold = None
        high_demand_multiplier = None
        very_high_demand_multiplier = None

        if config.pricing_config is not None:
            pc = config.pricing_config
            price_per_km = pc.price_per_km
            demand_window_minutes = pc.demand_window_minutes
            high_demand_threshold = pc.high_demand_threshold
            very_high_demand_threshold = pc.very_high_demand_threshold
            high_demand_multiplier = pc.high_demand_multiplier
            very_high_demand_multiplier = pc.very_high_demand_multiplier
            weekday_multipliers = [
                WeekdayMultiplierDto(week_day=day.value, multiplier=multiplier)
                for day, multiplier in pc.weekday_multipliers.items()
            ]

        return GetDeliveryConfigurationResponse(
            business_config_id=config.business_config_id,
            base_shipping_cost=config.base_shipping_cost,
            origin_address_id=config.origin_address_id,
            available_zone=available_zone,
            price_per_km=price_per_km,
            demand_window_minutes=demand_window_minutes,
            high_demand_threshold=high_demand_threshold,
            very_high_demand_threshold=very_high_demand_threshold,
            high_demand_multiplier=high_demand_multiplier,
            very_high_demand_multiplier=very_high_demand_multiplier,
            weekday_multipliers=weekday_multipliers,
            is_configured=config.is_fully_configured,
        )
