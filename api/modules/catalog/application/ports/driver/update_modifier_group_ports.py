from dataclasses import dataclass
from typing import Optional, Protocol

@dataclass(frozen=True)
class UpdateModifierGroupCommand:
    group_id: str
    name: Optional[str] = None
    min_selections: Optional[int] = None
    max_selections: Optional[int] = None

@dataclass(frozen=True)
class UpdateModifierGroupResponse:
    id: str
    name: str
    min_selections: int
    max_selections: int

class UpdateModifierGroupPort(Protocol):
    def execute(self, command: UpdateModifierGroupCommand) -> UpdateModifierGroupResponse: ...
