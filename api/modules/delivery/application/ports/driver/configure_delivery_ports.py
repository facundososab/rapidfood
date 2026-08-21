"""Configure delivery driver port.

Defines the command, response, and protocol for the use case that lets a
restaurant owner configure their full delivery setup.
"""

from __future__ import annotations

from abc import ABC, abstractmethod
from dataclasses import dataclass, field
from decimal import Decimal
from typing import Any, Dict, List, Optional


@dataclass
class WeekdayMultiplierInput:
    """A single weekday multiplier entry."""

    week_day: str  # WeekDay enum value, e.g. "MONDAY"
    multiplier: Decimal


@dataclass
class CoordinateInput:
    """A single [longitude, latitude] pair from the GeoJSON input."""

    longitude: float
    latitude: float


@dataclass
class DeliveryZoneInput:
    """GeoJSON-style polygon input from the HTTP layer."""

    # exterior_ring: list of [longitude, latitude] coordinate pairs
    exterior_ring: List[CoordinateInput]
    holes: List[List[CoordinateInput]] = field(default_factory=list)


@dataclass
class ConfigureDeliveryCommand:
    """Command for setting up or updating delivery configuration."""

    business_config_id: str
    base_shipping_cost: Decimal
    origin_address_id: str
    delivery_zone: DeliveryZoneInput
    price_per_km: Decimal
    high_demand_threshold: int
    very_high_demand_threshold: int
    high_demand_multiplier: Decimal
    very_high_demand_multiplier: Decimal
    demand_window_minutes: int
    weekday_multipliers: List[WeekdayMultiplierInput]


@dataclass(frozen=True)
class ConfigureDeliveryResponse:
    """Confirmation that delivery was configured successfully."""

    business_config_id: str


class ConfigureDeliveryPort(ABC):
    """Driver port for configuring delivery."""

    @abstractmethod
    def execute(self, command: ConfigureDeliveryCommand) -> ConfigureDeliveryResponse:
        ...
