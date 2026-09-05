"""In-memory fakes for all delivery driven ports.

These stubs implement the driven port Protocols and can be composed
in any way the test needs without touching Prisma, ORS, or Shapely.
"""

from __future__ import annotations

from datetime import datetime, timezone
from decimal import Decimal
from typing import Dict, List, Optional, Tuple

from modules.delivery.application.ports.driven.business_address_query_port import (
    AddressSnapshot,
    BusinessAddressQueryPort,
)
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
from modules.delivery.domain.errors.delivery_errors import (
    AddressCouldNotBeGeocodedError,
    GeocodingProviderError,
    InvalidDeliveryZoneError,
    RoutingProviderError,
)
from modules.delivery.domain.models.coordinates import Coordinates
from modules.delivery.domain.models.delivery_configuration import DeliveryConfiguration
from modules.delivery.domain.models.delivery_zone import DeliveryZone
from modules.delivery.domain.models.postal_address import PostalAddress
from modules.delivery.domain.models.route_metrics import RouteMetrics


class InMemoryDeliveryConfigurationRepository(DeliveryConfigurationRepositoryPort):
    """In-memory repository keyed by business_config_id."""

    def __init__(self) -> None:
        self._store: Dict[str, DeliveryConfiguration] = {}

    def get_by_business_config_id(
        self, business_config_id: str
    ) -> Optional[DeliveryConfiguration]:
        return self._store.get(business_config_id)

    def save(self, config: DeliveryConfiguration) -> None:
        self._store[config.business_config_id] = config


class FakeBusinessAddressQuery(BusinessAddressQueryPort):
    """Fake address query that returns pre-seeded address snapshots."""

    def __init__(self, addresses: Optional[Dict[str, AddressSnapshot]] = None) -> None:
        self._addresses: Dict[str, AddressSnapshot] = addresses or {}

    def add(self, address_id: str, business_config_id: str) -> None:
        self._addresses[address_id] = AddressSnapshot(
            address_id=address_id,
            business_config_id=business_config_id,
        )

    def get_by_id(self, address_id: str) -> Optional[AddressSnapshot]:
        return self._addresses.get(address_id)


class AlwaysValidGeometryPort(DeliveryZoneGeometryPort):
    """Geometry adapter that accepts any polygon and always returns True for covers()."""

    def validate_and_normalize(self, zone: DeliveryZone) -> DeliveryZone:
        return zone

    def covers(self, zone: DeliveryZone, point: Coordinates) -> bool:
        return True


class AlwaysOutsideGeometryPort(DeliveryZoneGeometryPort):
    """Geometry adapter that always returns False for covers() (outside zone)."""

    def validate_and_normalize(self, zone: DeliveryZone) -> DeliveryZone:
        return zone

    def covers(self, zone: DeliveryZone, point: Coordinates) -> bool:
        return False


class RejectingGeometryPort(DeliveryZoneGeometryPort):
    """Geometry adapter that always raises InvalidDeliveryZoneError."""

    def validate_and_normalize(self, zone: DeliveryZone) -> DeliveryZone:
        raise InvalidDeliveryZoneError("Polygon is invalid (fake).")

    def covers(self, zone: DeliveryZone, point: Coordinates) -> bool:
        return False


class FixedGeocodingPort(GeocodingProviderPort):
    """Returns a pre-configured Coordinates for any address."""

    def __init__(self, result: Coordinates) -> None:
        self._result = result

    def geocode(self, address: PostalAddress) -> Coordinates:
        return self._result


class FailingGeocodingPort(GeocodingProviderPort):
    """Always raises AddressCouldNotBeGeocodedError."""

    def geocode(self, address: PostalAddress) -> Coordinates:
        raise AddressCouldNotBeGeocodedError("Cannot geocode (fake).")


class ErrorGeocodingPort(GeocodingProviderPort):
    """Always raises GeocodingProviderError (simulates provider failure)."""

    def geocode(self, address: PostalAddress) -> Coordinates:
        raise GeocodingProviderError("Provider is down (fake).")


class FixedRoutingPort(RoutingProviderPort):
    """Returns a fixed RouteMetrics for any pair of coordinates."""

    def __init__(self, distance_km: float, duration_minutes: float) -> None:
        self._metrics = RouteMetrics(
            distance_km=distance_km,
            duration_minutes=duration_minutes,
        )

    def calculate_route(
        self, origin: Coordinates, destination: Coordinates
    ) -> RouteMetrics:
        return self._metrics


class FailingRoutingPort(RoutingProviderPort):
    """Always raises RoutingProviderError."""

    def calculate_route(
        self, origin: Coordinates, destination: Coordinates
    ) -> RouteMetrics:
        raise RoutingProviderError("Routing provider is down (fake).")


class FixedDemandPort(OrderDemandProviderPort):
    """Returns a fixed count for all demand queries."""

    def __init__(self, count: int = 0) -> None:
        self._count = count

    def count_recent_active_delivery_orders(
        self, business_config_id: str, since: datetime
    ) -> int:
        return self._count


class PerBusinessDemandPort(OrderDemandProviderPort):
    """Returns per-business counts — useful for restaurant isolation tests."""

    def __init__(self, counts: Dict[str, int]) -> None:
        self._counts = counts

    def count_recent_active_delivery_orders(
        self, business_config_id: str, since: datetime
    ) -> int:
        return self._counts.get(business_config_id, 0)


class FixedClock(ClockPort):
    """Clock that always returns the same instant."""

    def __init__(self, now: Optional[datetime] = None) -> None:
        self._now = now or datetime(2026, 1, 6, 12, 0, 0, tzinfo=timezone.utc)  # Monday noon UTC

    def utc_now(self) -> datetime:
        return self._now
