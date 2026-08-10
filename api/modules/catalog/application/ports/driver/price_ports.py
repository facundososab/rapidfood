from dataclasses import dataclass
from datetime import date
from decimal import Decimal
from typing import Protocol


@dataclass(frozen=True)
class AddPriceCommand:
    product_id: str
    since_date: date
    price: Decimal

@dataclass(frozen=True)
class AddPriceResponse:
    id: str
    product_id: str
    since_date: date
    price: Decimal

class AddPricePort(Protocol):
    def execute(self, command: AddPriceCommand) -> AddPriceResponse: ...
