"""ShapelyDeliveryZoneAdapter — geometry driven adapter.

Implements DeliveryZoneGeometryPort using Shapely. All Shapely imports
are confined to this file. Domain and application layers never see
shapely types.

Validation checks:
    - Minimum 4 points in the exterior ring
    - Polygon can be constructed without error
    - Polygon is not empty
    - Polygon has non-zero area
    - Polygon is valid (no self-intersections etc.)

Point-in-polygon uses Shapely's `covers()` which returns True for
points on the boundary (unlike `contains()` which excludes the boundary).
"""

from __future__ import annotations

import logging
from typing import List

from shapely.geometry import Point, Polygon
from shapely.validation import explain_validity

from modules.delivery.application.ports.driven.delivery_zone_geometry_port import (
    DeliveryZoneGeometryPort,
)
from modules.delivery.domain.errors.delivery_errors import InvalidDeliveryZoneError
from modules.delivery.domain.models.coordinates import Coordinates
from modules.delivery.domain.models.delivery_zone import DeliveryZone

logger = logging.getLogger(__name__)


def _ring_to_shapely(ring: List[Coordinates]) -> List[tuple]:
    """Convert domain Coordinates ring to Shapely (lon, lat) tuples."""
    return [(c.longitude, c.latitude) for c in ring]


def _zone_to_shapely(zone: DeliveryZone) -> Polygon:
    """Convert a DeliveryZone to a Shapely Polygon."""
    exterior = _ring_to_shapely(zone.exterior_ring)
    holes = [_ring_to_shapely(hole) for hole in zone.holes]
    return Polygon(exterior, holes)


class ShapelyDeliveryZoneAdapter(DeliveryZoneGeometryPort):
    """Geometry adapter backed by Shapely."""

    def validate_and_normalize(self, zone: DeliveryZone) -> DeliveryZone:
        """Validate polygon and return normalized zone.

        Raises:
            InvalidDeliveryZoneError: If the polygon is invalid.
        """
        try:
            polygon = _zone_to_shapely(zone)
        except Exception as exc:
            raise InvalidDeliveryZoneError(
                f"Could not construct polygon: {exc}"
            ) from exc

        if polygon.is_empty:
            raise InvalidDeliveryZoneError("Delivery zone polygon is empty.")

        if polygon.area == 0:
            raise InvalidDeliveryZoneError(
                "Delivery zone polygon has zero area (all points are collinear)."
            )

        if not polygon.is_valid:
            reason = explain_validity(polygon)
            raise InvalidDeliveryZoneError(
                f"Delivery zone polygon is invalid: {reason}"
            )

        logger.debug(
            "Delivery zone validated: area=%.6f, valid=%s",
            polygon.area,
            polygon.is_valid,
        )
        # Return the original zone; Shapely has validated it without modifying domain data.
        return zone

    def covers(self, zone: DeliveryZone, point: Coordinates) -> bool:
        """Return True if the zone covers the point (boundary inclusive)."""
        polygon = _zone_to_shapely(zone)
        shapely_point = Point(point.longitude, point.latitude)
        return polygon.covers(shapely_point)
