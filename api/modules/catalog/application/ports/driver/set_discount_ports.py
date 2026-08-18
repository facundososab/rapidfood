from dataclasses import dataclass
from decimal import Decimal
from typing import Optional, Protocol


@dataclass(frozen=True)
class SetDiscountCommand:
    percentage: Decimal
    product_id: Optional[str] = None


@dataclass(frozen=True)
class SetDiscountResponse:
    id: str
    percentage: Decimal
    product_id: Optional[str]


class SetDiscountPort(Protocol):
    def execute(self, command: SetDiscountCommand) -> SetDiscountResponse: ...