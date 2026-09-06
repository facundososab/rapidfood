from dataclasses import dataclass
from decimal import Decimal
from datetime import date
from typing import Optional, Protocol

@dataclass(frozen=True)
class SetVariantPriceCommand:
    product_variant_id: str
    price: Decimal
    since_date: Optional[date] = None

@dataclass(frozen=True)
class SetVariantPriceResponse:
    price_id: str
    product_variant_id: str
    price: Decimal
    since_date: date

class SetVariantPricePort(Protocol):
    def execute(self, command: SetVariantPriceCommand) -> SetVariantPriceResponse: ...
