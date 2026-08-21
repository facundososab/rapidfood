"""DeliveryZone domain model.

A polygon representing the geographic area where a restaurant delivers.
Stored as lists of Coordinates rings (exterior + optional holes).
No Shapely types leak here — conversion is the geometry adapter's responsibility.

GeoJSON coordinate order [longitude, latitude] is handled in adapters;
the domain always works with Coordinates(latitude, longitude).
"""

from __future__ import annotations

from dataclasses import dataclass, field
from typing import List

from modules.delivery.domain.models.coordinates import Coordinates


@dataclass
class DeliveryZone:
    """Geographic polygon defining the delivery area.

    exterior_ring: ordered list of Coordinates forming the polygon boundary.
                   The first and last point should be equal (closed ring).
    holes:         optional list of interior rings representing exclusion areas.
    """

    exterior_ring: List[Coordinates]
    holes: List[List[Coordinates]] = field(default_factory=list)

    def __post_init__(self) -> None:
        if len(self.exterior_ring) < 4:
            raise ValueError(
                "A polygon exterior ring needs at least 4 points "
                "(3 unique + closing point)."
            )
