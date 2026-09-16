from dataclasses import dataclass
from typing import Protocol

@dataclass(frozen=True)
class UpdateIngredientCommand:
    ingredient_id: str
    name: str

@dataclass(frozen=True)
class UpdateIngredientResponse:
    id: str
    name: str

class UpdateIngredientPort(Protocol):
    def execute(self, command: UpdateIngredientCommand) -> UpdateIngredientResponse: ...
