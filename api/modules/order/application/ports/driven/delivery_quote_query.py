"""Driven port: obtain a real delivery quote for a destination address.

Implemented by an adapter that delegates to the delivery module's
CalculateDeliveryQuotePort. Keeps the order module free of delivery internals.
"""
from abc import ABC, abstractmethod
from dataclasses import dataclass
from decimal import Decimal
from typing import Optional

from modules.order.domain.models.delivery_address import DeliveryAddress


@dataclass
class DeliveryQuoteSnapshot:
    available: bool
    shipping_cost: Optional[Decimal] = None
    distance_km: Optional[float] = None
    estimated_duration_minutes: Optional[float] = None
    demand_level: Optional[str] = None


class DeliveryQuoteQuery(ABC):
    @abstractmethod
    def quote(
        self, business_config_id: str, destination: DeliveryAddress
    ) -> DeliveryQuoteSnapshot:
        ...
