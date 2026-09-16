from dataclasses import dataclass
from typing import Protocol

@dataclass(frozen=True)
class CreateModifierGroupCommand:
    product_id: str
    name: str
    min_selections: int
    max_selections: int

@dataclass(frozen=True)
class CreateModifierGroupResponse:
    id: str
    product_id: str
    name: str
    min_selections: int
    max_selections: int

class CreateModifierGroupPort(Protocol):
    def execute(self, command: CreateModifierGroupCommand) -> CreateModifierGroupResponse: ...
