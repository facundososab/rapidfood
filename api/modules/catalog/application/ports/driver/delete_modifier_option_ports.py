from dataclasses import dataclass
from typing import Protocol


@dataclass(frozen=True)
class DeleteModifierOptionCommand:
    option_id: str


@dataclass(frozen=True)
class DeleteModifierOptionResponse:
    id: str


class DeleteModifierOptionPort(Protocol):
    def execute(self, command: DeleteModifierOptionCommand) -> DeleteModifierOptionResponse: ...
