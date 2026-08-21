"""GetDeliveryConfiguration driver port.

Returns the current delivery configuration for a restaurant so the admin
panel can display and edit it.
"""

from __future__ import annotations

from abc import ABC, abstractmethod
from dataclasses import dataclass, field
from decimal import Decimal
from typing import Any, Dict, List, Optional


@dataclass(frozen=True)
class GetDeliveryConfigurationQuery:
    """Query for retrieving delivery configuration."""

    business_config_id: str


@dataclass
class WeekdayMultiplierDto:
    week_day: str
    multiplier: Decimal


@dataclass
class GetDeliveryConfigurationResponse:
    """Delivery configuration response DTO."""

    business_config_id: str
    base_shipping_cost: Decimal
    origin_address_id: Optional[str]
    # None = zone not configured yet; dict = GeoJSON Polygon
    available_zone: Optional[Dict[str, Any]]
    price_per_km: Optional[Decimal]
    demand_window_minutes: Optional[int]
    high_demand_threshold: Optional[int]
    very_high_demand_threshold: Optional[int]
    high_demand_multiplier: Optional[Decimal]
    very_high_demand_multiplier: Optional[Decimal]
    weekday_multipliers: List[WeekdayMultiplierDto] = field(default_factory=list)
    is_configured: bool = False


class GetDeliveryConfigurationPort(ABC):
    """Driver port for reading delivery configuration."""

    @abstractmethod
    def execute(
        self, query: GetDeliveryConfigurationQuery
    ) -> GetDeliveryConfigurationResponse:
        ...
