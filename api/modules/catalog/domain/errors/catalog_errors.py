class DomainError(Exception):
    """Error base para el dominio de catalogo."""

class ProductNotFoundError(DomainError):
    def __init__(self, product_id: str) -> None:
        super().__init__(f"No existe un producto con id {product_id}")
        self.product_id = product_id

class CategoryNotFoundError(DomainError):
    def __init__(self, category_id: str) -> None:
        super().__init__(f"No existe una categoria con id {category_id}")
        self.category_id = category_id

class ProductWithoutPriceError(DomainError):
    def __init__(self, product_id: str) -> None:
        super().__init__(f"El producto {product_id} no tiene un precio vigente")
        self.product_id = product_id

class ProductInUseError(DomainError):
    def __init__(self, product_id: str) -> None:
        super().__init__(f"El producto {product_id} no puede eliminarse porque está en uso")
        self.product_id = product_id

class VariantNotFoundError(DomainError):
    def __init__(self, variant_id: str) -> None:
        super().__init__(f"No variant found with id {variant_id}")
        self.variant_id = variant_id

class IngredientNotFoundError(DomainError):
    def __init__(self, ingredient_id: str) -> None:
        super().__init__(f"No ingredient found with id {ingredient_id}")
        self.ingredient_id = ingredient_id

class ModifierGroupNotFoundError(DomainError):
    def __init__(self, group_id: str) -> None:
        super().__init__(f"No modifier group found with id {group_id}")
        self.group_id = group_id

class ModifierOptionNotFoundError(DomainError):
    def __init__(self, option_id: str) -> None:
        super().__init__(f"No modifier option found with id {option_id}")
        self.option_id = option_id

class InvalidModifierGroupError(DomainError):
    pass

class InvalidDiscountTargetError(DomainError):
    pass