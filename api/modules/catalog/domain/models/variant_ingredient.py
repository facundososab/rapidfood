from dataclasses import dataclass


@dataclass
class VariantIngredient:
    """Association between a ProductVariant and an Ingredient."""
    id: str
    product_variant_id: str
    ingredient_id: str
    ingredient_name: str
    removable: bool = True
