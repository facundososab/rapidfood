"""RoutingProviderPort — driven port.

Abstracts the external routing/directions service. The use case receives
normalized RouteMetrics (km, minutes) regardless of what the underlying
provider returns (meters, seconds, etc.).
"""

from __future__ import annotations

from typing import Protocol

from modules.delivery.domain.models.coordinates import Coordinates
from modules.delivery.domain.models.route_metrics import RouteMetrics


class RoutingProviderPort(Protocol):
    """Driven port for street-distance routing between two points."""

    def calculate_route(
        self,
        origin: Coordinates,
        destination: Coordinates,
    ) -> RouteMetrics:
        """Return route metrics for driving from origin to destination.

        Raises:
            RoutingProviderError: If the provider fails for technical reasons.
        """
        ...
