"""Preparation-time (ETA) configuration for a restaurant.

Its demand thresholds are INDEPENDENT from delivery pricing: the price and the
preparation time may react to different order volumes. Validation lives in
``__post_init__`` so an invalid config can never exist.
"""
from __future__ import annotations

from dataclasses import dataclass

from modules.order.domain.errors.order_errors import InvalidPreparationTimeConfigError


@dataclass(frozen=True)
class PreparationTimeConfig:
    high_demand_threshold: int
    very_high_demand_threshold: int
    normal_prep_minutes: int
    high_demand_prep_minutes: int
    very_high_demand_prep_minutes: int
    buffer_minutes: int

    def __post_init__(self) -> None:
        if self.high_demand_threshold < 0:
            raise InvalidPreparationTimeConfigError(
                "high_demand_threshold must be >= 0"
            )
        if self.very_high_demand_threshold <= self.high_demand_threshold:
            raise InvalidPreparationTimeConfigError(
                "very_high_demand_threshold must be > high_demand_threshold"
            )
        if self.normal_prep_minutes <= 0:
            raise InvalidPreparationTimeConfigError(
                "normal_prep_minutes must be > 0"
            )
        if self.high_demand_prep_minutes < self.normal_prep_minutes:
            raise InvalidPreparationTimeConfigError(
                "high_demand_prep_minutes must be >= normal_prep_minutes"
            )
        if self.very_high_demand_prep_minutes < self.high_demand_prep_minutes:
            raise InvalidPreparationTimeConfigError(
                "very_high_demand_prep_minutes must be >= high_demand_prep_minutes"
            )
        if self.buffer_minutes < 0:
            raise InvalidPreparationTimeConfigError("buffer_minutes must be >= 0")

    @classmethod
    def default(cls) -> "PreparationTimeConfig":
        """Fallback used when a business has not configured its ETA yet."""
        return cls(
            high_demand_threshold=8,
            very_high_demand_threshold=15,
            normal_prep_minutes=20,
            high_demand_prep_minutes=35,
            very_high_demand_prep_minutes=50,
            buffer_minutes=5,
        )
