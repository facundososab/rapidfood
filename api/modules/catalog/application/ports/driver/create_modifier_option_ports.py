from dataclasses import dataclass
from decimal import Decimal
from typing import Protocol

@dataclass(frozen=True)
class CreateModifierOptionCommand:
    modifier_group_id: str
    name: str
    price_delta: Decimal

@dataclass(frozen=True)
class CreateModifierOptionResponse:
    id: str
    modifier_group_id: str
    name: str
    price_delta: Decimal
    available: bool

class CreateModifierOptionPort(Protocol):
    def execute(self, command: CreateModifierOptionCommand) -> CreateModifierOptionResponse: ...
