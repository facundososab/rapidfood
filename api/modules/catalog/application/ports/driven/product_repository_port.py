from typing import Protocol
from modules.catalog.domain.models.product import Product, ProductState



class ProductRepositoryPort(Protocol):
    def save(self, product: Product) -> None: ...

    def find_by_id(self, product_id: str) -> Product | None: ...

    def list(
        self,
        category_id: str | None = None,
        state: ProductState | None = None,
    ) -> list[Product]: ...

    def delete(self, product_id: str) -> None: ...