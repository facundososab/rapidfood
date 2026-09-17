"""Infrastructure tests for the Photon geocoding adapter."""

from __future__ import annotations

import pytest

from modules.delivery.domain.errors.delivery_errors import (
    AddressCouldNotBeGeocodedError,
    GeocodingProviderError,
)
from modules.delivery.domain.models.coordinates import Coordinates
from modules.delivery.domain.models.postal_address import PostalAddress
from modules.delivery.infrastructure.adapters.driven.geocoding import (
    photon_geocoding_adapter,
)
from modules.delivery.infrastructure.adapters.driven.geocoding.photon_geocoding_adapter import (
    PhotonGeocodingAdapter,
)


def _address() -> PostalAddress:
    return PostalAddress(
        street="Avenida Génova",
        street_number="9531",
        city="Rosario",
        province="Santa Fe",
    )


class _Response:
    def __init__(self, payload: dict, status_code: int = 200) -> None:
        self._payload = payload
        self.status_code = status_code

    def raise_for_status(self) -> None:
        if self.status_code >= 400:
            raise RuntimeError(f"HTTP {self.status_code}")

    def json(self) -> dict:
        return self._payload


def test_geocode_returns_coordinates_lat_lon(monkeypatch):
    captured: dict = {}

    def fake_get(url, params=None, headers=None, timeout=None):
        captured.update(url=url, params=params, headers=headers)
        return _Response(
            {"features": [{"geometry": {"coordinates": [-60.773803, -32.917750]}}]}
        )

    monkeypatch.setattr(photon_geocoding_adapter.requests, "get", fake_get)

    coords = PhotonGeocodingAdapter().geocode(_address())

    assert coords == Coordinates(latitude=-32.917750, longitude=-60.773803)
    assert captured["params"]["q"] == "Avenida Génova 9531, Rosario, Santa Fe"
    assert captured["params"]["bbox"]
    # Photon's edge returns 403 without a User-Agent.
    assert captured["headers"].get("User-Agent")


def test_geocode_raises_when_no_features(monkeypatch):
    monkeypatch.setattr(
        photon_geocoding_adapter.requests, "get", lambda *a, **k: _Response({"features": []})
    )

    with pytest.raises(AddressCouldNotBeGeocodedError):
        PhotonGeocodingAdapter().geocode(_address())


def test_geocode_raises_when_coordinates_missing(monkeypatch):
    monkeypatch.setattr(
        photon_geocoding_adapter.requests,
        "get",
        lambda *a, **k: _Response({"features": [{"geometry": {"coordinates": []}}]}),
    )

    with pytest.raises(AddressCouldNotBeGeocodedError):
        PhotonGeocodingAdapter().geocode(_address())


def test_geocode_wraps_transport_errors(monkeypatch):
    def boom(*a, **k):
        raise RuntimeError("connection refused")

    monkeypatch.setattr(photon_geocoding_adapter.requests, "get", boom)

    with pytest.raises(GeocodingProviderError):
        PhotonGeocodingAdapter().geocode(_address())
