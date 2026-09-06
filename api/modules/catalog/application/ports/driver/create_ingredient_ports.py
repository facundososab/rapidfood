from dataclasses import dataclass
from typing import Protocol

@dataclass(frozen=True)
class CreateIngredientCommand:
    name: str

@dataclass(frozen=True)
class CreateIngredientResponse:
    id: str
    name: str

class CreateIngredientPort(Protocol):
    def execute(self, command: CreateIngredientCommand) -> CreateIngredientResponse: ...
