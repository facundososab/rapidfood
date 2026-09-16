"""OpenRouteServiceGeocodingAdapter — geocoding driven adapter.

Implements GeocodingProviderPort using the openrouteservice Python SDK.
All ORS imports and API response handling are confined to this file.

The OPENROUTESERVICE_API_KEY is read from Django settings (which reads it
from the environment variable of the same name). It is NEVER logged.
"""

from __future__ import annotations

import logging
from typing import Any, Dict

import openrouteservice
from django.conf import settings

from modules.delivery.application.ports.driven.geocoding_provider_port import (
    GeocodingProviderPort,
)
from modules.delivery.domain.errors.delivery_errors import (
    AddressCouldNotBeGeocodedError,
    GeocodingProviderError,
)
from modules.delivery.domain.models.coordinates import Coordinates
from modules.delivery.domain.models.postal_address import PostalAddress

logger = logging.getLogger(__name__)


class OpenRouteServiceGeocodingAdapter(GeocodingProviderPort):
    """Geocoding adapter backed by OpenRouteService Pelias geocoder."""

    def __init__(self, api_key: str) -> None:
        # api_key is injected by the container — never read settings here directly.
        self._client = openrouteservice.Client(key=api_key)

    def geocode(self, address: PostalAddress) -> Coordinates:
        """Geocode a postal address to coordinates.

        Raises:
            AddressCouldNotBeGeocodedError: No result found.
            GeocodingProviderError: Provider returned an unexpected error.
        """
        query = address.geocoding_query()
        logger.debug("Geocoding address: %s", query)

        try:
            result: Dict[str, Any] = self._client.pelias_search(text=query)
        except Exception as exc:
            logger.error("Geocoding provider error for query '%s': %s", query, exc)
            raise GeocodingProviderError(
                f"Geocoding provider failed: {exc}"
            ) from exc

        features = result.get("features", [])
        if not features:
            logger.warning("No geocoding result for address: %s", query)
            raise AddressCouldNotBeGeocodedError(
                f"Could not geocode address: {query}"
            )

        # GeoJSON: coordinates are [longitude, latitude]
        geometry = features[0].get("geometry", {})
        coords = geometry.get("coordinates", [])
        if len(coords) < 2:
            raise AddressCouldNotBeGeocodedError(
                f"Geocoding result has invalid coordinates for: {query}"
            )

        longitude, latitude = coords[0], coords[1]
        logger.debug(
            "Geocoded '%s' -> lat=%.6f lon=%.6f", query, latitude, longitude
        )
        return Coordinates(latitude=latitude, longitude=longitude)
