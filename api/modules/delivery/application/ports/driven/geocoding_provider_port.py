"""GeocodingProviderPort — driven port.

Abstracts the external geocoding service so the use case has no knowledge
of OpenRouteService, API keys, or HTTP request/response shapes.
"""

from __future__ import annotations

from typing import Protocol

from modules.delivery.domain.models.coordinates import Coordinates
from modules.delivery.domain.models.postal_address import PostalAddress


class GeocodingProviderPort(Protocol):
    """Driven port for converting a postal address to geographic coordinates."""

    def geocode(self, address: PostalAddress) -> Coordinates:
        """Return coordinates for the given address.

        Raises:
            AddressCouldNotBeGeocodedError: If the provider finds no match.
            GeocodingProviderError: If the provider fails for technical reasons.
        """
        ...
