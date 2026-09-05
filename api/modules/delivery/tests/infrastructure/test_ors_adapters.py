"""Infrastructure tests for ORS geocoding and routing adapters."""

from __future__ import annotations

import httpx
import pytest

from modules.delivery.domain.errors.delivery_errors import (
    AddressCouldNotBeGeocodedError,
    GeocodingProviderError,
    RoutingProviderError,
)
from modules.delivery.domain.models.coordinates import Coordinates
from modules.delivery.domain.models.postal_address import PostalAddress
from modules.delivery.infrastructure.adapters.driven.geocoding.ors_geocoding_adapter import (
    OpenRouteServiceGeocodingAdapter,
)
from modules.delivery.infrastructure.adapters.driven.routing.ors_routing_adapter import (
    OpenRouteServiceRoutingAdapter,
)


class FakeResponse:
    def __init__(self, status_code: int, json_data: dict):
        self.status_code = status_code
        self._json = json_data

    def json(self):
        return self._json

    def raise_for_status(self):
        if self.status_code >= 400:
            raise httpx.HTTPStatusError("Error", request=None, response=self)


class FakeClient:
    def __init__(self, responses: dict):
        self.responses = responses
        self.calls = []

    def pelias_search(self, **kwargs):
        self.calls.append(("pelias_search", kwargs))
        response = self.responses.get("pelias_search", FakeResponse(404, {}))
        response.raise_for_status()
        return response.json()

    def directions(self, **kwargs):
        self.calls.append(("directions", kwargs))
        response = self.responses.get("directions", FakeResponse(404, {}))
        response.raise_for_status()
        return response.json()


@pytest.fixture
def fake_address():
    return PostalAddress(
        street="Av. Corrientes",
        street_number="1234",
        city="CABA",
        province="Buenos Aires",
    )


# ---------------------------------------------------------------------------
# Geocoding Tests
# ---------------------------------------------------------------------------

class TestOpenRouteServiceGeocodingAdapter:
    def test_geocode_success(self, fake_address):
        client = FakeClient({
            "pelias_search": FakeResponse(200, {
                "features": [
                    {
                        "geometry": {
                            "coordinates": [-58.3816, -34.6037]  # [lon, lat]
                        }
                    }
                ]
            })
        })
        adapter = OpenRouteServiceGeocodingAdapter(api_key="fake")
        adapter._client = client

        coords = adapter.geocode(fake_address)

        assert coords.latitude == -34.6037
        assert coords.longitude == -58.3816
        
        # Verify call args
        url, kwargs = client.calls[0]
        assert kwargs["text"] == "Av. Corrientes 1234, CABA, Buenos Aires"

    def test_geocode_empty_results_raises(self, fake_address):
        client = FakeClient({
            "pelias_search": FakeResponse(200, {
                "features": []
            })
        })
        adapter = OpenRouteServiceGeocodingAdapter(api_key="fake")
        adapter._client = client

        with pytest.raises(AddressCouldNotBeGeocodedError):
            adapter.geocode(fake_address)

    def test_geocode_http_error_raises_provider_error(self, fake_address):
        client = FakeClient({
            "pelias_search": FakeResponse(500, {})
        })
        adapter = OpenRouteServiceGeocodingAdapter(api_key="fake")
        adapter._client = client

        with pytest.raises(GeocodingProviderError):
            adapter.geocode(fake_address)


# ---------------------------------------------------------------------------
# Routing Tests
# ---------------------------------------------------------------------------

class TestOpenRouteServiceRoutingAdapter:
    def test_routing_success(self):
        client = FakeClient({
            "directions": FakeResponse(200, {
                "routes": [
                    {
                        "summary": {
                            "distance": 2500,  # meters
                            "duration": 600,   # seconds
                        }
                    }
                ]
            })
        })
        adapter = OpenRouteServiceRoutingAdapter(api_key="fake")
        adapter._client = client

        origin = Coordinates(latitude=-34.6, longitude=-58.4)
        dest = Coordinates(latitude=-34.61, longitude=-58.41)

        metrics = adapter.calculate_route(origin, dest)

        # 2500m -> 2.5km; 600s -> 10.0m
        assert metrics.distance_km == 2.5
        assert metrics.duration_minutes == 10.0

        # Verify call args
        url, kwargs = client.calls[0]
        assert kwargs["coordinates"] == [
            [-58.4, -34.6],    # [lon, lat]
            [-58.41, -34.61],  # [lon, lat]
        ]

    def test_routing_http_error_raises_provider_error(self):
        client = FakeClient({
            "directions": FakeResponse(400, {})
        })
        adapter = OpenRouteServiceRoutingAdapter(api_key="fake")
        adapter._client = client

        origin = Coordinates(latitude=-34.6, longitude=-58.4)
        dest = Coordinates(latitude=-34.61, longitude=-58.41)

        with pytest.raises(RoutingProviderError):
            adapter.calculate_route(origin, dest)

    def test_routing_malformed_response_raises(self):
        client = FakeClient({
            "directions": FakeResponse(200, {
                "routes": []  # missing summary
            })
        })
        adapter = OpenRouteServiceRoutingAdapter(api_key="fake")
        adapter._client = client

        origin = Coordinates(latitude=-34.6, longitude=-58.4)
        dest = Coordinates(latitude=-34.61, longitude=-58.41)

        with pytest.raises(RoutingProviderError, match="Unexpected"):
            adapter.calculate_route(origin, dest)
