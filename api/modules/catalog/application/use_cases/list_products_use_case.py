from modules.catalog.application.ports.driver.list_products_ports import (
    ListProductsPort,
    ListProductsQuery,
    ProductSummary,
)
from modules.catalog.application.ports.driven.product_repository_port import (
    ProductRepositoryPort,
)


class ListProductsUseCase(ListProductsPort):
    def __init__(self, products: ProductRepositoryPort) -> None:
        self._products = products

    def execute(self, query: ListProductsQuery) -> list[ProductSummary]:
        products = self._products.list(category_id=query.category_id, state=query.state)
        return [
            ProductSummary(
                id=p.id, description=p.description, state=p.state.value, category_id=p.category_id
            )
            for p in products
        ]