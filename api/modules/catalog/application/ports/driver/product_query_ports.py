from dataclasses import dataclass, field
from decimal import Decimal
from typing import Optional, Protocol, Tuple

@dataclass(frozen=True)
class IngredientSnapshot:
    ingredient_id: str
    name: str
    removable: bool

@dataclass(frozen=True)
class ModifierOptionSnapshot:
    option_id: str
    name: str
    price_delta: Decimal
    available: bool

@dataclass(frozen=True)
class ModifierGroupSnapshot:
    group_id: str
    name: str
    min_selections: int
    max_selections: int
    options: Tuple[ModifierOptionSnapshot, ...] = field(default_factory=tuple)

@dataclass(frozen=True)
class VariantSnapshot:
    variant_id: str
    variant_name: str
    price: Decimal
    is_available: bool  # product.available AND variant.available
    ingredients: Tuple[IngredientSnapshot, ...] = field(default_factory=tuple)

@dataclass(frozen=True)
class ProductSnapshot:
    product_id: str
    name: str
    is_available: bool
    variants: Tuple[VariantSnapshot, ...] = field(default_factory=tuple)
    modifier_groups: Tuple[ModifierGroupSnapshot, ...] = field(default_factory=tuple)

@dataclass(frozen=True)
class VariantContext:
    """
    All data the order module needs to validate and price a variant line.
    """
    product_id: str
    product_name: str
    product_available: bool
    variant_id: str
    variant_name: str
    variant_available: bool
    current_price: Decimal
    ingredients: Tuple[IngredientSnapshot, ...] = field(default_factory=tuple)
    modifier_groups: Tuple[ModifierGroupSnapshot, ...] = field(default_factory=tuple)

    @property
    def is_sellable(self) -> bool:
        return self.product_available and self.variant_available

class ProductQueryPort(Protocol):
    def find_product(self, product_id: str) -> Optional[ProductSnapshot]: ...
    def find_variant_context(self, variant_id: str) -> Optional[VariantContext]: ...
