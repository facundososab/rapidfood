from __future__ import annotations

from dataclasses import dataclass
from decimal import Decimal

@dataclass(frozen=True)
class GetBusinessConfigurationQuery:
    business_config_id: str

@dataclass(frozen=True)
class GetBusinessConfigurationResult:
    id: str
    businessName: str
    minOrder: Decimal
    shippingCost: Decimal
    businessHours: list
    addresses: list
