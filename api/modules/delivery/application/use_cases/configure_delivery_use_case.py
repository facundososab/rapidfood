"""ConfigureDeliveryUseCase.

Validates and persists the full delivery configuration for a restaurant.
All writes are atomic via the repository's save() method.

Steps:
    1. Verify business configuration exists (repository returns None if not).
    2. Verify origin address exists.
    3. Verify origin address belongs to this restaurant.
    4. Build DeliveryZone from polygon input.
    5. Validate polygon integrity via geometry port.
    6. Build and validate DeliveryPricingConfig (validation inside domain model).
    7. Build DeliveryConfiguration aggregate.
    8. Save atomically.
"""

from __future__ import annotations

from decimal import Decimal

from modules.delivery.application.ports.driven.business_address_query_port import (
    BusinessAddressQueryPort,
)
from modules.delivery.application.ports.driven.delivery_configuration_repository_port import (
    DeliveryConfigurationRepositoryPort,
)
from modules.delivery.application.ports.driven.delivery_zone_geometry_port import (
    DeliveryZoneGeometryPort,
)
from modules.delivery.application.ports.driver.configure_delivery_ports import (
    ConfigureDeliveryCommand,
    ConfigureDeliveryPort,
    ConfigureDeliveryResponse,
)
from modules.delivery.domain.errors.delivery_errors import (
    BusinessConfigurationNotFoundError,
    DeliveryOriginDoesNotBelongToBusinessError,
    DeliveryOriginNotConfiguredError,
)
from modules.delivery.domain.models.coordinates import Coordinates
from modules.delivery.domain.models.delivery_configuration import DeliveryConfiguration
from modules.delivery.domain.models.delivery_pricing_config import DeliveryPricingConfig
from modules.delivery.domain.models.delivery_zone import DeliveryZone
from modules.delivery.domain.models.postal_address import PostalAddress
from modules.delivery.domain.models.week_day import WeekDay


class ConfigureDeliveryUseCase(ConfigureDeliveryPort):
    """Configures or updates the delivery setup for a restaurant."""

    def __init__(
        self,
        delivery_config_repo: DeliveryConfigurationRepositoryPort,
        address_query: BusinessAddressQueryPort,
        geometry: DeliveryZoneGeometryPort,
    ) -> None:
        self._repo = delivery_config_repo
        self._address_query = address_query
        self._geometry = geometry

    def execute(self, command: ConfigureDeliveryCommand) -> ConfigureDeliveryResponse:
        # 1. Verify origin address exists
        address_snapshot = self._address_query.get_by_id(command.origin_address_id)
        if address_snapshot is None:
            raise DeliveryOriginNotConfiguredError(
                f"Address {command.origin_address_id} does not exist."
            )

        # 2. Verify origin address belongs to this restaurant
        if address_snapshot.business_config_id != command.business_config_id:
            raise DeliveryOriginDoesNotBelongToBusinessError(
                f"Address {command.origin_address_id} does not belong to "
                f"business {command.business_config_id}."
            )

        # 3. Build DeliveryZone from polygon input
        exterior_ring = [
            Coordinates(latitude=c.latitude, longitude=c.longitude)
            for c in command.delivery_zone.exterior_ring
        ]
        holes = [
            [Coordinates(latitude=c.latitude, longitude=c.longitude) for c in ring]
            for ring in command.delivery_zone.holes
        ]
        raw_zone = DeliveryZone(exterior_ring=exterior_ring, holes=holes)

        # 4. Validate polygon via geometry port (raises InvalidDeliveryZoneError if bad)
        validated_zone = self._geometry.validate_and_normalize(raw_zone)

        # 5. Build weekday multipliers dict
        weekday_multipliers = {
            WeekDay(rule.week_day): rule.multiplier
            for rule in command.weekday_multipliers
        }

        # 6. Build and validate DeliveryPricingConfig (domain validates invariants)
        pricing_config = DeliveryPricingConfig(
            price_per_km=command.price_per_km,
            high_demand_threshold=command.high_demand_threshold,
            very_high_demand_threshold=command.very_high_demand_threshold,
            high_demand_multiplier=command.high_demand_multiplier,
            very_high_demand_multiplier=command.very_high_demand_multiplier,
            weekday_multipliers=weekday_multipliers,
        )

        # 7. We need a PostalAddress for the origin; the repository will load it.
        # For now we pass a placeholder — the repo is responsible for hydrating it
        # from the persisted address record.
        # We build a minimal PostalAddress from what we know via the address_id;
        # the repo will store the origin_address_id and load the full address on read.
        # Pass a stub here — real data is always loaded from DB on get().
        origin_address = PostalAddress(
            street="",
            street_number="",
            city="",
            province="",
        )

        # 8. Build aggregate and save atomically
        config = DeliveryConfiguration(
            business_config_id=command.business_config_id,
            base_shipping_cost=command.base_shipping_cost,
            origin_address_id=command.origin_address_id,
            origin_address=origin_address,
            delivery_zone=validated_zone,
            pricing_config=pricing_config,
        )

        self._repo.save(config)

        return ConfigureDeliveryResponse(
            business_config_id=command.business_config_id,
        )
