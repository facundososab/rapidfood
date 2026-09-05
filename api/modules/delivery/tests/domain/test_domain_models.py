"""Domain tests for domain models (Coordinates, DeliveryZone, DeliveryPricingConfig)."""

from __future__ import annotations

from decimal import Decimal
from typing import Dict

import pytest

from modules.delivery.domain.errors.delivery_errors import (
    IncompleteWeekdayPricingRulesError,
    InvalidDeliveryPricingConfigurationError,
)
from modules.delivery.domain.models.coordinates import Coordinates
from modules.delivery.domain.models.delivery_pricing_config import DeliveryPricingConfig
from modules.delivery.domain.models.delivery_zone import DeliveryZone
from modules.delivery.domain.models.week_day import WeekDay


def _all_weekday_multipliers(value: Decimal = Decimal("1.00")) -> Dict[WeekDay, Decimal]:
    return {day: value for day in WeekDay}


# ---------------------------------------------------------------------------
# Coordinates
# ---------------------------------------------------------------------------

class TestCoordinates:
    def test_valid(self):
        c = Coordinates(latitude=-34.6, longitude=-58.4)
        assert c.latitude == -34.6
        assert c.longitude == -58.4

    def test_latitude_out_of_range(self):
        with pytest.raises(ValueError, match="Latitude"):
            Coordinates(latitude=91.0, longitude=0.0)

    def test_longitude_out_of_range(self):
        with pytest.raises(ValueError, match="Longitude"):
            Coordinates(latitude=0.0, longitude=181.0)

    def test_south_pole(self):
        Coordinates(latitude=-90.0, longitude=0.0)  # no raise

    def test_north_pole(self):
        Coordinates(latitude=90.0, longitude=0.0)  # no raise


# ---------------------------------------------------------------------------
# DeliveryZone
# ---------------------------------------------------------------------------

def _make_square_zone() -> DeliveryZone:
    """A simple 4-point square ring (closed)."""
    return DeliveryZone(
        exterior_ring=[
            Coordinates(0.0, 0.0),
            Coordinates(1.0, 0.0),
            Coordinates(1.0, 1.0),
            Coordinates(0.0, 0.0),  # closing point
        ]
    )


class TestDeliveryZone:
    def test_valid_zone(self):
        zone = _make_square_zone()
        assert len(zone.exterior_ring) == 4

    def test_too_few_points_raises(self):
        with pytest.raises(ValueError, match="4 points"):
            DeliveryZone(
                exterior_ring=[
                    Coordinates(0.0, 0.0),
                    Coordinates(1.0, 0.0),
                    Coordinates(0.0, 0.0),
                ]
            )

    def test_with_holes(self):
        zone = DeliveryZone(
            exterior_ring=[
                Coordinates(0.0, 0.0),
                Coordinates(2.0, 0.0),
                Coordinates(2.0, 2.0),
                Coordinates(0.0, 0.0),
            ],
            holes=[
                [
                    Coordinates(0.5, 0.5),
                    Coordinates(1.5, 0.5),
                    Coordinates(1.5, 1.5),
                    Coordinates(0.5, 0.5),
                ]
            ],
        )
        assert len(zone.holes) == 1


# ---------------------------------------------------------------------------
# DeliveryPricingConfig
# ---------------------------------------------------------------------------

class TestDeliveryPricingConfig:
    def test_valid_config(self):
        config = DeliveryPricingConfig(
            price_per_km=Decimal("10.00"),
            high_demand_threshold=5,
            very_high_demand_threshold=10,
            high_demand_multiplier=Decimal("1.50"),
            very_high_demand_multiplier=Decimal("2.00"),
            weekday_multipliers=_all_weekday_multipliers(),
        )
        assert config.price_per_km == Decimal("10.00")

    def test_negative_price_per_km_raises(self):
        with pytest.raises(InvalidDeliveryPricingConfigurationError):
            DeliveryPricingConfig(
                price_per_km=Decimal("-1.00"),
                high_demand_threshold=5,
                very_high_demand_threshold=10,
                high_demand_multiplier=Decimal("1.50"),
                very_high_demand_multiplier=Decimal("2.00"),
                weekday_multipliers=_all_weekday_multipliers(),
            )

    def test_very_high_must_be_greater_than_high(self):
        with pytest.raises(InvalidDeliveryPricingConfigurationError):
            DeliveryPricingConfig(
                price_per_km=Decimal("150.00"),
                high_demand_threshold=5,
                high_demand_multiplier=Decimal("1.50"),
                very_high_demand_multiplier=Decimal("2.00"),
                weekday_multipliers=_all_weekday_multipliers(),
            )

    def test_equal_thresholds_raise(self):
        with pytest.raises(InvalidDeliveryPricingConfigurationError):
            DeliveryPricingConfig(
                price_per_km=Decimal("10.00"),
                high_demand_threshold=10,
                very_high_demand_threshold=10,
                high_demand_multiplier=Decimal("1.50"),
                very_high_demand_multiplier=Decimal("2.00"),
                demand_window_minutes=30,
                weekday_multipliers=_all_weekday_multipliers(),
            )

    def test_zero_multiplier_raises(self):
        with pytest.raises(InvalidDeliveryPricingConfigurationError):
            DeliveryPricingConfig(
                price_per_km=Decimal("10.00"),
                high_demand_threshold=5,
                very_high_demand_threshold=10,
                high_demand_multiplier=Decimal("0"),
                very_high_demand_multiplier=Decimal("2.00"),
                demand_window_minutes=30,
                weekday_multipliers=_all_weekday_multipliers(),
            )

    def test_missing_weekday_raises(self):
        partial = {day: Decimal("1.00") for day in list(WeekDay)[:6]}  # missing Sunday
        with pytest.raises(IncompleteWeekdayPricingRulesError):
            DeliveryPricingConfig(
                price_per_km=Decimal("10.00"),
                high_demand_threshold=5,
                very_high_demand_threshold=10,
                high_demand_multiplier=Decimal("1.50"),
                very_high_demand_multiplier=Decimal("2.00"),
                demand_window_minutes=30,
                weekday_multipliers=partial,
            )

    def test_weekday_multiplier_zero_raises(self):
        multipliers = _all_weekday_multipliers()
        multipliers[WeekDay.MONDAY] = Decimal("0")
        with pytest.raises(InvalidDeliveryPricingConfigurationError, match="MONDAY"):
            DeliveryPricingConfig(
                price_per_km=Decimal("10.00"),
                high_demand_threshold=5,
                very_high_demand_threshold=10,
                high_demand_multiplier=Decimal("1.50"),
                very_high_demand_multiplier=Decimal("2.00"),
                demand_window_minutes=30,
                weekday_multipliers=multipliers,
            )
