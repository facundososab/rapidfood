"""Domain tests for the demand_classifier service."""

from __future__ import annotations

from decimal import Decimal
from typing import Dict

import pytest

from modules.delivery.domain.models.demand_level import DemandLevel
from modules.delivery.domain.models.delivery_pricing_config import DeliveryPricingConfig
from modules.delivery.domain.models.week_day import WeekDay
from modules.delivery.domain.services.demand_classifier import classify_demand


def _all_weekday_multipliers(value: Decimal = Decimal("1.00")) -> Dict[WeekDay, Decimal]:
    return {day: value for day in WeekDay}


@pytest.fixture()
def pricing_config() -> DeliveryPricingConfig:
    return DeliveryPricingConfig(
        price_per_km=Decimal("10.00"),
        high_demand_threshold=5,
        very_high_demand_threshold=10,
        high_demand_multiplier=Decimal("1.50"),
        very_high_demand_multiplier=Decimal("2.00"),
        demand_window_minutes=30,
        weekday_multipliers=_all_weekday_multipliers(),
    )


class TestNormalDemand:
    def test_zero_orders_is_normal(self, pricing_config):
        level, multiplier = classify_demand(0, pricing_config)
        assert level == DemandLevel.NORMAL
        assert multiplier == Decimal("1.00")

    def test_below_threshold_is_normal(self, pricing_config):
        level, multiplier = classify_demand(4, pricing_config)
        assert level == DemandLevel.NORMAL
        assert multiplier == Decimal("1.00")


class TestHighDemand:
    def test_at_threshold_is_high(self, pricing_config):
        level, multiplier = classify_demand(5, pricing_config)
        assert level == DemandLevel.HIGH
        assert multiplier == Decimal("1.50")

    def test_between_thresholds_is_high(self, pricing_config):
        level, multiplier = classify_demand(9, pricing_config)
        assert level == DemandLevel.HIGH
        assert multiplier == Decimal("1.50")


class TestVeryHighDemand:
    def test_at_very_high_threshold_is_very_high(self, pricing_config):
        level, multiplier = classify_demand(10, pricing_config)
        assert level == DemandLevel.VERY_HIGH
        assert multiplier == Decimal("2.00")

    def test_way_above_threshold(self, pricing_config):
        level, multiplier = classify_demand(999, pricing_config)
        assert level == DemandLevel.VERY_HIGH
        assert multiplier == Decimal("2.00")
