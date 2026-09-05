"""Coordinates value object.

Represents a geographic point with validated latitude/longitude.
The domain always uses (latitude, longitude) order. GeoJSON/ORS coordinate
inversion ([longitude, latitude]) is handled exclusively in adapters.
"""

from __future__ import annotations

from dataclasses import dataclass


@dataclass(frozen=True)
class Coordinates:
    """Immutable geographic coordinates."""

    latitude: float
    longitude: float

    def __post_init__(self) -> None:
        if not (-90.0 <= self.latitude <= 90.0):
            raise ValueError(
                f"Latitude must be between -90 and 90, got {self.latitude}"
            )
        if not (-180.0 <= self.longitude <= 180.0):
            raise ValueError(
                f"Longitude must be between -180 and 180, got {self.longitude}"
            )
