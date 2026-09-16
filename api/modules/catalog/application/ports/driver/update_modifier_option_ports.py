from dataclasses import dataclass
from decimal import Decimal
from typing import Optional, Protocol

@dataclass(frozen=True)
class UpdateModifierOptionCommand:
    option_id: str
    name: Optional[str] = None
    price_delta: Optional[Decimal] = None
    available: Optional[bool] = None

@dataclass(frozen=True)
class UpdateModifierOptionResponse:
    id: str
    name: str
    price_delta: Decimal
    available: bool

class UpdateModifierOptionPort(Protocol):
    def execute(self, command: UpdateModifierOptionCommand) -> UpdateModifierOptionResponse: ...
