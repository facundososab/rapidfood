"""DeliveryZoneGeometryPort — driven port.

Abstracts Shapely (or any other geometry engine) for polygon validation
and point-in-polygon tests. The domain and application layers are
completely unaware of Shapely types.
"""

from __future__ import annotations

from typing import Protocol

from modules.delivery.domain.models.coordinates import Coordinates
from modules.delivery.domain.models.delivery_zone import DeliveryZone


class DeliveryZoneGeometryPort(Protocol):
    """Driven port for geometric operations on delivery zones."""

    def validate_and_normalize(self, zone: DeliveryZone) -> DeliveryZone:
        """Validate polygon integrity and return a normalized zone.

        Raises:
            InvalidDeliveryZoneError: If the polygon is invalid (self-intersecting,
                too few points, zero area, etc.).
        """
        ...

    def covers(self, zone: DeliveryZone, point: Coordinates) -> bool:
        """Return True if the zone covers the point (includes boundary).

        Uses 'covers' semantics: a point exactly on the polygon boundary
        is considered inside the zone.
        """
        ...
