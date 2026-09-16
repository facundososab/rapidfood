from dataclasses import dataclass
from decimal import Decimal
from datetime import date
from typing import Optional, Protocol

@dataclass(frozen=True)
class CreateVariantCommand:
    product_id: str
    name: str
    initial_price: Decimal
    price_since_date: Optional[date] = None

@dataclass(frozen=True)
class CreateVariantResponse:
    id: str
    product_id: str
    name: str
    available: bool
    current_price: Decimal

class CreateVariantPort(Protocol):
    def execute(self, command: CreateVariantCommand) -> CreateVariantResponse: ...
