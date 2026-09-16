"""DeliveryQuote result model.

Represents the result of a delivery quote calculation.
When available=False the optional fields are all None.
The quote is ephemeral — it is never automatically persisted.
"""

from __future__ import annotations

from dataclasses import dataclass
from decimal import Decimal
from typing import Optional

from modules.delivery.domain.models.demand_level import DemandLevel


@dataclass(frozen=True)
class DeliveryQuote:
    """Result of a delivery quote calculation for a given destination."""

    available: bool
    distance_km: Optional[float] = None
    estimated_duration_minutes: Optional[float] = None
    shipping_cost: Optional[Decimal] = None
    demand_level: Optional[DemandLevel] = None

    @classmethod
    def unavailable(cls) -> "DeliveryQuote":
        """Factory for the 'outside zone' case."""
        return cls(available=False)
