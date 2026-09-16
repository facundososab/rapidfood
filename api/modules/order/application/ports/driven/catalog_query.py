from abc import ABC, abstractmethod
from typing import Optional
from dataclasses import dataclass, field
from decimal import Decimal


@dataclass(frozen=True)
class IngredientInfo:
    ingredient_id: str
    name: str
    removable: bool


@dataclass(frozen=True)
class ModifierOptionInfo:
    option_id: str
    name: str
    price_delta: Decimal
    available: bool


@dataclass(frozen=True)
class ModifierGroupInfo:
    group_id: str
    name: str
    min_selections: int
    max_selections: int
    options: tuple = field(default_factory=tuple)  # tuple[ModifierOptionInfo, ...]


@dataclass(frozen=True)
class VariantContext:
    """
    All data needed to validate and price an OrderLine.
    Fetched from the catalog at order-line creation and confirmation time.
    """
    product_id: str
    product_name: str
    product_available: bool
    variant_id: str
    variant_name: str
    variant_available: bool
    current_price: Decimal
    ingredients: tuple = field(default_factory=tuple)  # tuple[IngredientInfo, ...]
    modifier_groups: tuple = field(default_factory=tuple)  # tuple[ModifierGroupInfo, ...]

    @property
    def is_sellable(self) -> bool:
        """Both product AND variant must be available."""
        return self.product_available and self.variant_available


# Keep old ProductSnapshot for backward compatibility during transition
@dataclass
class ProductSnapshot:
    product_id: str
    price: Decimal
    is_available: bool


class CatalogQuery(ABC):
    """Driven port: fetch catalog data needed by the order module."""

    @abstractmethod
    def get_variant_context(self, variant_id: str) -> Optional[VariantContext]:
        """Return full context for a variant (price, ingredients, modifiers)."""
        pass
