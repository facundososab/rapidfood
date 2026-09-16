"""Infrastructure tests for ShapelyDeliveryZoneAdapter."""

from __future__ import annotations

import pytest

from modules.delivery.domain.errors.delivery_errors import InvalidDeliveryZoneError
from modules.delivery.domain.models.coordinates import Coordinates
from modules.delivery.domain.models.delivery_zone import DeliveryZone
from modules.delivery.infrastructure.adapters.driven.geometry.shapely_delivery_zone_adapter import (
    ShapelyDeliveryZoneAdapter,
)


@pytest.fixture()
def adapter() -> ShapelyDeliveryZoneAdapter:
    return ShapelyDeliveryZoneAdapter()


def _ba_zone() -> DeliveryZone:
    """A simple valid polygon around a Buenos Aires block."""
    return DeliveryZone(
        exterior_ring=[
            Coordinates(latitude=-34.60, longitude=-58.38),
            Coordinates(latitude=-34.60, longitude=-58.37),
            Coordinates(latitude=-34.61, longitude=-58.37),
            Coordinates(latitude=-34.61, longitude=-58.38),
            Coordinates(latitude=-34.60, longitude=-58.38),  # closed
        ]
    )


class TestValidation:
    def test_valid_polygon_passes(self, adapter):
        zone = _ba_zone()
        result = adapter.validate_and_normalize(zone)
        assert result is zone  # same object returned

    def test_collinear_points_raises(self, adapter):
        """Three collinear points form a zero-area polygon."""
        zone = DeliveryZone(
            exterior_ring=[
                Coordinates(0.0, 0.0),
                Coordinates(0.0, 1.0),
                Coordinates(0.0, 2.0),
                Coordinates(0.0, 0.0),
            ]
        )
        with pytest.raises(InvalidDeliveryZoneError, match="area"):
            adapter.validate_and_normalize(zone)

    def test_self_intersecting_polygon_raises(self, adapter):
        """Figure-8 polygon is invalid."""
        zone = DeliveryZone(
            exterior_ring=[
                Coordinates(0.0, 0.0),
                Coordinates(2.0, 2.0),
                Coordinates(2.0, 0.0),
                Coordinates(0.0, 2.0),
                Coordinates(0.0, 0.0),
            ]
        )
        with pytest.raises(InvalidDeliveryZoneError, match="invalid|zero area|collinear"):
            adapter.validate_and_normalize(zone)


class TestPointInPolygon:
    def test_point_inside(self, adapter):
        zone = _ba_zone()
        point = Coordinates(latitude=-34.605, longitude=-58.375)
        assert adapter.covers(zone, point) is True

    def test_point_outside(self, adapter):
        zone = _ba_zone()
        point = Coordinates(latitude=-35.0, longitude=-59.0)
        assert adapter.covers(zone, point) is False

    def test_point_on_boundary(self, adapter):
        zone = _ba_zone()
        # Exactly on the left edge
        point = Coordinates(latitude=-34.605, longitude=-58.38)
        assert adapter.covers(zone, point) is True
