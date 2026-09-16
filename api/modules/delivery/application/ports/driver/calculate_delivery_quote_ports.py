"""CalculateDeliveryQuote driver port.

Defines the contract for obtaining a real-time delivery quote for a
customer's destination address. Used by REST adapters and by other
bounded contexts (e.g., conversation).
"""

from __future__ import annotations

from abc import ABC, abstractmethod
from dataclasses import dataclass
from decimal import Decimal
from typing import Optional


@dataclass(frozen=True)
class AddressInput:
    """Customer destination address for quote calculation."""

    street: str
    street_number: str
    city: str
    province: str
    floor: Optional[str] = None
    apartment: Optional[str] = None
    postal_code: Optional[str] = None


@dataclass(frozen=True)
class CalculateDeliveryQuoteCommand:
    """Command for requesting a delivery quote."""

    business_config_id: str
    destination_address: AddressInput


@dataclass(frozen=True)
class CalculateDeliveryQuoteResponse:
    """Result of a delivery quote calculation."""

    available: bool
    distance_km: Optional[float] = None
    estimated_duration_minutes: Optional[float] = None
    shipping_cost: Optional[Decimal] = None
    demand_level: Optional[str] = None  # DemandLevel.value for serialization


class CalculateDeliveryQuotePort(ABC):
    """Driver port for calculating delivery quotes."""

    @abstractmethod
    def execute(
        self, command: CalculateDeliveryQuoteCommand
    ) -> CalculateDeliveryQuoteResponse:
        ...
