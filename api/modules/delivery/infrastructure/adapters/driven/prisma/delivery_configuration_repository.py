"""DeliveryConfigurationRepository — Prisma-backed driven adapter.

Maps between the Prisma schema and the DeliveryConfiguration domain aggregate.

Read strategy (get_by_business_config_id):
    1. Query BusinessConfiguration with include={deliveryPricingConfiguration:
       {include: {weekdayRules: True, originAddress: True}}, addresses: False}
    2. Also query BusinessConfiguration.availableZone (Json? field)
    3. Map everything to domain objects

Write strategy (save):
    Wraps all writes in a Prisma transaction (db.client.tx()) to maintain
    atomicity when upserting DeliveryPricingConfiguration + weekday rules
    and updating BusinessConfiguration.availableZone.

GeoJSON polygon storage:
    BusinessConfiguration.availableZone is stored as a GeoJSON Polygon dict.
    Exterior ring coordinates are [longitude, latitude] (GeoJSON standard).
    The domain uses Coordinates(latitude, longitude).
    Conversion is handled here — never in domain code.
"""

from __future__ import annotations

import logging
from decimal import Decimal
from typing import Any, Dict, List, Optional

from prisma import Prisma
from prisma.fields import Json

from modules.delivery.application.ports.driven.delivery_configuration_repository_port import (
    DeliveryConfigurationRepositoryPort,
)
from modules.delivery.domain.errors.delivery_errors import (
    BusinessConfigurationNotFoundError,
)
from modules.delivery.domain.models.coordinates import Coordinates
from modules.delivery.domain.models.delivery_configuration import DeliveryConfiguration
from modules.delivery.domain.models.delivery_pricing_config import DeliveryPricingConfig
from modules.delivery.domain.models.delivery_zone import DeliveryZone
from modules.delivery.domain.models.postal_address import PostalAddress
from modules.delivery.domain.models.week_day import WeekDay

logger = logging.getLogger(__name__)


def _geojson_to_zone(geojson: Dict[str, Any]) -> DeliveryZone:
    """Convert a GeoJSON Polygon dict to a domain DeliveryZone.

    GeoJSON: coordinates[0] = exterior ring, coordinates[1..] = holes.
    Each coordinate is [longitude, latitude].
    """
    rings: List[List[List[float]]] = geojson.get("coordinates", [])
    if not rings:
        raise ValueError("GeoJSON polygon has no coordinates")

    def parse_ring(ring: List[List[float]]) -> List[Coordinates]:
        return [
            Coordinates(latitude=coords[1], longitude=coords[0])
            for coords in ring
        ]

    exterior = parse_ring(rings[0])
    holes = [parse_ring(ring) for ring in rings[1:]]
    return DeliveryZone(exterior_ring=exterior, holes=holes)


def _zone_to_geojson(zone: DeliveryZone) -> Dict[str, Any]:
    """Convert a domain DeliveryZone to a GeoJSON Polygon dict."""
    def ring_to_coords(ring: List[Coordinates]) -> List[List[float]]:
        return [[c.longitude, c.latitude] for c in ring]

    coordinates = [ring_to_coords(zone.exterior_ring)]
    for hole in zone.holes:
        coordinates.append(ring_to_coords(hole))
    return {"type": "Polygon", "coordinates": coordinates}


def _prisma_address_to_postal(row: Any) -> PostalAddress:
    """Map a Prisma Address row to a PostalAddress value object."""
    return PostalAddress(
        street=row.street,
        street_number=row.streetNumber,
        city=row.city,
        province=row.province,
        floor=row.floor,
        apartment=row.apartment,
        postal_code=row.postalCode,
    )


class DeliveryConfigurationRepository(DeliveryConfigurationRepositoryPort):
    """Reads and writes the full delivery configuration via Prisma."""

    def __init__(self, db: Prisma) -> None:
        self._db = db

    def get_by_business_config_id(
        self, business_config_id: str
    ) -> Optional[DeliveryConfiguration]:
        """Load the aggregate from Prisma, or return None."""
        biz = self._db.businessconfiguration.find_unique(
            where={"id": business_config_id},
            include={
                "deliveryPricingConfiguration": {
                    "include": {
                        "weekdayRules": True,
                        "originAddress": True,
                    }
                }
            },
        )

        if biz is None:
            logger.debug("BusinessConfiguration not found: %s", business_config_id)
            return None

        delivery_zone: Optional[DeliveryZone] = None
        if biz.availableZone is not None:
            try:
                delivery_zone = _geojson_to_zone(biz.availableZone)
            except Exception as exc:
                logger.error(
                    "Failed to parse availableZone for business %s: %s",
                    business_config_id,
                    exc,
                )
                delivery_zone = None

        pricing_config: Optional[DeliveryPricingConfig] = None
        origin_address_id: Optional[str] = None
        origin_address: Optional[PostalAddress] = None

        dpc = biz.deliveryPricingConfiguration
        if dpc is not None:
            origin_address_id = dpc.originAddressId
            origin_address = _prisma_address_to_postal(dpc.originAddress)
            weekday_multipliers = {
                WeekDay(getattr(rule.weekDay, "value", rule.weekDay)): rule.multiplier
                for rule in dpc.weekdayRules
            }
            try:
                pricing_config = DeliveryPricingConfig(
                    price_per_km=dpc.pricePerKm,
                    high_demand_threshold=dpc.highDemandThreshold,
                    very_high_demand_threshold=dpc.veryHighDemandThreshold,
                    high_demand_multiplier=Decimal(str(dpc.highDemandMultiplier)),
                    very_high_demand_multiplier=Decimal(str(dpc.veryHighDemandMultiplier)),
                    weekday_multipliers=weekday_multipliers,
                )
            except Exception as exc:
                logger.error(
                    "Corrupt DeliveryPricingConfig for business %s: %s",
                    business_config_id,
                    exc,
                )
                pricing_config = None

        return DeliveryConfiguration(
            business_config_id=business_config_id,
            base_shipping_cost=biz.shippingCost,
            origin_address_id=origin_address_id or "",
            origin_address=origin_address or PostalAddress(
                street="", street_number="", city="", province=""
            ),
            delivery_zone=delivery_zone,
            pricing_config=pricing_config,
        )

    def save(self, config: DeliveryConfiguration) -> None:
        """Atomically persist the full delivery configuration.

        Uses Prisma transaction to ensure:
        - BusinessConfiguration.availableZone is updated
        - DeliveryPricingConfiguration is upserted
        - All 7 WeekdayPricingRules are replaced atomically
        """
        geojson = None
        if config.delivery_zone is not None:
            geojson = _zone_to_geojson(config.delivery_zone)

        pricing = config.pricing_config

        with self._db.tx() as tx:
            # Update the delivery zone on BusinessConfiguration.
            # `availableZone` is a Json? column: prisma-client-python only
            # treats values wrapped in `Json(...)` as raw JSON (a raw dict is
            # interpreted as a query "Data" node and raises DataError).
            tx.businessconfiguration.update(
                where={"id": config.business_config_id},
                data={"availableZone": Json(geojson) if geojson is not None else None},
            )

            if pricing is not None:
                # Upsert the DeliveryPricingConfiguration
                upsert_data = {
                    "businessConfigId": config.business_config_id,
                    "originAddressId": config.origin_address_id,
                    "pricePerKm": pricing.price_per_km,
                    "highDemandThreshold": pricing.high_demand_threshold,
                    "veryHighDemandThreshold": pricing.very_high_demand_threshold,
                    "highDemandMultiplier": pricing.high_demand_multiplier,
                    "veryHighDemandMultiplier": pricing.very_high_demand_multiplier,
                }

                dpc = tx.deliverypricingconfiguration.upsert(
                    where={"businessConfigId": config.business_config_id},
                    data={
                        "create": upsert_data,
                        "update": {
                            k: v for k, v in upsert_data.items()
                            if k != "businessConfigId"
                        },
                    },
                )

                # Delete existing weekday rules and recreate
                tx.deliveryweekdaypricingrule.delete_many(
                    where={"deliveryPricingConfigId": dpc.id}
                )
                for day, multiplier in pricing.weekday_multipliers.items():
                    tx.deliveryweekdaypricingrule.create(
                        data={
                            "deliveryPricingConfigId": dpc.id,
                            "weekDay": day.value,
                            "multiplier": multiplier,
                        }
                    )
