"""DeliveryPricingConfig domain model.

Contains all per-restaurant pricing rules. Validation of business invariants
is enforced in __post_init__ so that an invalid config can never be constructed.
"""

from __future__ import annotations

from dataclasses import dataclass
from decimal import Decimal
from typing import Dict

from modules.delivery.domain.errors.delivery_errors import (
    IncompleteWeekdayPricingRulesError,
    InvalidDeliveryPricingConfigurationError,
)
from modules.delivery.domain.models.week_day import WeekDay

_ALL_WEEKDAYS = set(WeekDay)


@dataclass
class DeliveryPricingConfig:
    """Per-restaurant delivery pricing configuration."""

    price_per_km: Decimal
    high_demand_threshold: int
    very_high_demand_threshold: int
    high_demand_multiplier: Decimal
    very_high_demand_multiplier: Decimal
    # One entry per WeekDay; all 7 must be present.
    weekday_multipliers: Dict[WeekDay, Decimal]

    def __post_init__(self) -> None:
        self._validate()

    def _validate(self) -> None:
        if self.price_per_km < Decimal("0"):
            raise InvalidDeliveryPricingConfigurationError(
                "price_per_km must be >= 0"
            )
        if self.high_demand_threshold < 0:
            raise InvalidDeliveryPricingConfigurationError(
                "high_demand_threshold must be >= 0"
            )
        if self.very_high_demand_threshold <= self.high_demand_threshold:
            raise InvalidDeliveryPricingConfigurationError(
                "very_high_demand_threshold must be > high_demand_threshold"
            )
        if self.high_demand_multiplier <= Decimal("0"):
            raise InvalidDeliveryPricingConfigurationError(
                "high_demand_multiplier must be > 0"
            )
        if self.very_high_demand_multiplier <= Decimal("0"):
            raise InvalidDeliveryPricingConfigurationError(
                "very_high_demand_multiplier must be > 0"
            )
        missing = _ALL_WEEKDAYS - set(self.weekday_multipliers.keys())
        if missing:
            missing_names = ", ".join(d.value for d in sorted(missing, key=lambda d: d.value))
            raise IncompleteWeekdayPricingRulesError(
                f"Missing weekday pricing rules for: {missing_names}"
            )
        for day, multiplier in self.weekday_multipliers.items():
            if multiplier <= Decimal("0"):
                raise InvalidDeliveryPricingConfigurationError(
                    f"Weekday multiplier for {day.value} must be > 0"
                )
