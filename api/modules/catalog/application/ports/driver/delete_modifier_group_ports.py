from dataclasses import dataclass
from typing import Protocol


@dataclass(frozen=True)
class DeleteModifierGroupCommand:
    group_id: str


@dataclass(frozen=True)
class DeleteModifierGroupResponse:
    id: str


class DeleteModifierGroupPort(Protocol):
    def execute(self, command: DeleteModifierGroupCommand) -> DeleteModifierGroupResponse: ...
