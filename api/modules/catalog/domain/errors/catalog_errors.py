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