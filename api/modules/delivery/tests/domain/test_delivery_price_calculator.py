"""Domain tests for the DeliveryPriceCalculator service."""

from __future__ import annotations

from decimal import Decimal

import pytest

from modules.delivery.domain.services.delivery_price_calculator import (
    DeliveryPriceCalculator,
)


@pytest.fixture()
def calc() -> DeliveryPriceCalculator:
    return DeliveryPriceCalculator()


class TestZeroDistance:
    def test_zero_distance_returns_base_cost(self, calc):
        result = calc.calculate(
            base_shipping_cost=Decimal("100.00"),
            distance_km=0.0,
            price_per_km=Decimal("20.00"),
            weekday_multiplier=Decimal("1.00"),
            demand_multiplier=Decimal("1.00"),
        )
        assert result == Decimal("100.00")


class TestDistanceCharge:
    def test_5km_at_20_per_km(self, calc):
        result = calc.calculate(
            base_shipping_cost=Decimal("50.00"),
            distance_km=5.0,
            price_per_km=Decimal("20.00"),
            weekday_multiplier=Decimal("1.00"),
            demand_multiplier=Decimal("1.00"),
        )
        # 50 + 5*20 = 150
        assert result == Decimal("150.00")

    def test_fractional_distance(self, calc):
        result = calc.calculate(
            base_shipping_cost=Decimal("0.00"),
            distance_km=2.5,
            price_per_km=Decimal("30.00"),
            weekday_multiplier=Decimal("1.00"),
            demand_multiplier=Decimal("1.00"),
        )
        # 0 + 2.5*30 = 75
        assert result == Decimal("75.00")


class TestWeekdayMultiplier:
    def test_weekend_surcharge(self, calc):
        result = calc.calculate(
            base_shipping_cost=Decimal("100.00"),
            distance_km=0.0,
            price_per_km=Decimal("0.00"),
            weekday_multiplier=Decimal("1.50"),
            demand_multiplier=Decimal("1.00"),
        )
        assert result == Decimal("150.00")


class TestDemandMultiplier:
    def test_high_demand_doubles_cost(self, calc):
        result = calc.calculate(
            base_shipping_cost=Decimal("100.00"),
            distance_km=0.0,
            price_per_km=Decimal("0.00"),
            weekday_multiplier=Decimal("1.00"),
            demand_multiplier=Decimal("2.00"),
        )
        assert result == Decimal("200.00")

    def test_normal_demand_multiplier_is_1(self, calc):
        base = Decimal("123.45")
        result = calc.calculate(
            base_shipping_cost=base,
            distance_km=0.0,
            price_per_km=Decimal("0.00"),
            weekday_multiplier=Decimal("1.00"),
            demand_multiplier=Decimal("1.00"),
        )
        assert result == base


class TestRounding:
    def test_rounds_half_up(self, calc):
        # 100 * 1.00 * 1.005 = 100.50 -> 100.50
        result = calc.calculate(
            base_shipping_cost=Decimal("100.00"),
            distance_km=0.0,
            price_per_km=Decimal("0.00"),
            weekday_multiplier=Decimal("1.005"),
            demand_multiplier=Decimal("1.00"),
        )
        # 100.00 * 1.005 = 100.500 -> ROUND_HALF_UP -> 100.50
        assert result == Decimal("100.50")

    def test_combined_formula(self, calc):
        # base=50, distance=3.5km, price=10, weekday=1.20, demand=1.50
        # distance_charge = 3.5 * 10 = 35
        # subtotal = 50 + 35 = 85
        # 85 * 1.20 = 102.00
        # 102.00 * 1.50 = 153.00
        result = calc.calculate(
            base_shipping_cost=Decimal("50.00"),
            distance_km=3.5,
            price_per_km=Decimal("10.00"),
            weekday_multiplier=Decimal("1.20"),
            demand_multiplier=Decimal("1.50"),
        )
        assert result == Decimal("153.00")
