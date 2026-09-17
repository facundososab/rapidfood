"""PhotonGeocodingAdapter — geocoding driven adapter.

Implements GeocodingProviderPort using Photon (komoot), the same OpenStreetMap
geocoder the admin panel uses in the browser. Keeping front and back on the same
geocoder avoids the mismatch where the zone drawn on the map and the coordinates
the quote resolves point to different places.

Photon needs no API key. The request is bounded to Argentina (same bbox as the
admin panel) to disambiguate street names.
"""

from __future__ import annotations

import logging
from typing import Any

import requests

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

_BASE_URL = "https://photon.komoot.io/api/"
# Argentina bbox (minLon, minLat, maxLon, maxLat) — same value the panel uses.
_AR_BBOX = "-73.56,-55.06,-53.64,-21.78"


class PhotonGeocodingAdapter(GeocodingProviderPort):
    """Geocoding adapter backed by Photon (OpenStreetMap)."""

    def __init__(self, base_url: str = _BASE_URL, timeout: float = 10.0) -> None:
        self._base_url = base_url
        self._timeout = timeout

    def geocode(self, address: PostalAddress) -> Coordinates:
        query = address.geocoding_query()
        logger.debug("Geocoding address via Photon: %s", query)

        try:
            response = requests.get(
                self._base_url,
                params={"q": query, "limit": 1, "bbox": _AR_BBOX},
                # Photon's edge rejects requests without a User-Agent (403).
                headers={"Accept": "application/json", "User-Agent": "rapidfood/1.0"},
                timeout=self._timeout,
            )
            response.raise_for_status()
            data: Any = response.json()
        except Exception as exc:
            logger.error("Geocoding provider error for query '%s': %s", query, exc)
            raise GeocodingProviderError(
                f"Geocoding provider failed: {exc}"
            ) from exc

        features = data.get("features") or []
        if not features:
            logger.warning("No geocoding result for address: %s", query)
            raise AddressCouldNotBeGeocodedError(
                f"Could not geocode address: {query}"
            )

        coordinates = features[0].get("geometry", {}).get("coordinates") or []
        if len(coordinates) < 2:
            raise AddressCouldNotBeGeocodedError(
                f"Geocoding result has invalid coordinates for: {query}"
            )

        # GeoJSON: coordinates are [longitude, latitude]
        longitude, latitude = coordinates[0], coordinates[1]
        logger.debug("Geocoded '%s' -> lat=%.6f lon=%.6f", query, latitude, longitude)
        return Coordinates(latitude=latitude, longitude=longitude)
