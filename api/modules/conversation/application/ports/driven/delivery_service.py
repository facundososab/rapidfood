"""Driven port: delivery quote for the agent.

Reuses the delivery module's existing quote capability; conversation never
computes shipping, geocodes or checks zones itself.
"""
from __future__ import annotations

from dataclasses import dataclass
from typing import Optional, Protocol


@dataclass(frozen=True, slots=True)
class DeliveryQuoteDTO:
    available: bool
    shipping_cost: Optional[str] = None
    distance_km: Optional[float] = None
    estimated_duration_minutes: Optional[float] = None
    demand_level: Optional[str] = None


class DeliveryServicePort(Protocol):
    def quote_delivery(
        self, business_configuration_id: str, destination_address: dict
    ) -> DeliveryQuoteDTO: ...
