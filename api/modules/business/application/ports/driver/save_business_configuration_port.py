from __future__ import annotations

from dataclasses import dataclass
from decimal import Decimal

@dataclass(frozen=True)
class SaveBusinessConfigurationCommand:
    business_config_id: str
    business_name: str
    min_order: Decimal
    shipping_cost: Decimal
