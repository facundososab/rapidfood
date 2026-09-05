"""OpenRouteServiceRoutingAdapter — routing driven adapter.

Implements RoutingProviderPort using the openrouteservice Python SDK.
All ORS imports and API response handling are confined to this file.

ORS returns distances in meters and durations in seconds.
This adapter converts them to kilometers and minutes before returning
the domain RouteMetrics object. Provider quirks never leak outward.
"""

from __future__ import annotations

import logging
from typing import Any, Dict, List

import openrouteservice
from openrouteservice import convert

from modules.delivery.application.ports.driven.routing_provider_port import (
    RoutingProviderPort,
)
from modules.delivery.domain.errors.delivery_errors import RoutingProviderError
from modules.delivery.domain.models.coordinates import Coordinates
from modules.delivery.domain.models.route_metrics import RouteMetrics

logger = logging.getLogger(__name__)

_METERS_TO_KM = 1 / 1000.0
_SECONDS_TO_MINUTES = 1 / 60.0


class OpenRouteServiceRoutingAdapter(RoutingProviderPort):
    """Routing adapter backed by OpenRouteService Directions API."""

    def __init__(self, api_key: str) -> None:
        self._client = openrouteservice.Client(key=api_key)

    def calculate_route(
        self,
        origin: Coordinates,
        destination: Coordinates,
    ) -> RouteMetrics:
        """Calculate driving route between two coordinates.

        ORS uses [longitude, latitude] coordinate order.

        Raises:
            RoutingProviderError: If ORS fails for any reason.
        """
        # ORS expects [longitude, latitude]
        coords: List[List[float]] = [
            [origin.longitude, origin.latitude],
            [destination.longitude, destination.latitude],
        ]
        logger.debug(
            "Calculating route from %s to %s",
            [origin.latitude, origin.longitude],
            [destination.latitude, destination.longitude],
        )

        try:
            result: Dict[str, Any] = self._client.directions(
                coordinates=coords,
                profile="driving-car",
                format="json",
            )
        except Exception as exc:
            logger.error("Routing provider error: %s", exc)
            raise RoutingProviderError(
                f"Routing provider failed: {exc}"
            ) from exc

        try:
            summary = result["routes"][0]["summary"]
            distance_m: float = summary["distance"]
            duration_s: float = summary["duration"]
        except (KeyError, IndexError) as exc:
            logger.error("Unexpected routing response shape: %s", result)
            raise RoutingProviderError(
                f"Unexpected response from routing provider: {exc}"
            ) from exc

        distance_km = distance_m * _METERS_TO_KM
        duration_minutes = duration_s * _SECONDS_TO_MINUTES

        logger.debug(
            "Route calculated: %.3f km, %.1f min", distance_km, duration_minutes
        )
        return RouteMetrics(
            distance_km=distance_km,
            duration_minutes=duration_minutes,
        )
