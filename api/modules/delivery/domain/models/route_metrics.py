"""RouteMetrics value object.

Contains the results of a street-distance routing calculation.
Distances and durations use normalized units (km, minutes) regardless
of what the underlying provider returns — conversion is the adapter's job.
"""

from __future__ import annotations

from dataclasses import dataclass


@dataclass(frozen=True)
class RouteMetrics:
    """Routing result in normalized units."""

    distance_km: float
    duration_minutes: float
