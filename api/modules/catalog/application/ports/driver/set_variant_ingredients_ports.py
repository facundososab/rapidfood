from dataclasses import dataclass, field
from typing import List, Protocol

@dataclass(frozen=True)
class IngredientEntry:
    ingredient_id: str
    removable: bool

@dataclass(frozen=True)
class SetVariantIngredientsCommand:
    variant_id: str
    entries: List[IngredientEntry] = field(default_factory=list)

@dataclass(frozen=True)
class VariantIngredientItem:
    id: str
    ingredient_id: str
    name: str
    removable: bool

@dataclass(frozen=True)
class SetVariantIngredientsResponse:
    variant_id: str
    ingredients: List[VariantIngredientItem] = field(default_factory=list)

class SetVariantIngredientsPort(Protocol):
    def execute(self, command: SetVariantIngredientsCommand) -> SetVariantIngredientsResponse: ...
