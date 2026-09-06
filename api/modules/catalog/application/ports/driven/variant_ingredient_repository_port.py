from typing import List, Protocol
from modules.catalog.domain.models.variant_ingredient import VariantIngredient

class SetIngredientEntry:
    ingredient_id: str
    removable: bool

class VariantIngredientRepositoryPort(Protocol):
    def set_ingredients(self, variant_id: str, entries: List[dict]) -> List[VariantIngredient]:
        """
        Replace all ingredients for a variant.
        Each entry: {'ingredient_id': str, 'removable': bool}
        """
        ...
    def list_for_variant(self, variant_id: str) -> List[VariantIngredient]: ...
