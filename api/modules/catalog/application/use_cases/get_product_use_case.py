from modules.catalog.application.ports.driver.get_product_ports import (
    GetProductPort,
    ProductDetail,
)
from modules.catalog.application.ports.driven.category_repository_port import (
    CategoryRepositoryPort,
)
from modules.catalog.application.ports.driven.price_repository_port import (
    PriceRepositoryPort,
)
from modules.catalog.application.ports.driven.product_repository_port import (
    ProductRepositoryPort,
)
from modules.catalog.domain.errors.catalog_errors import ProductNotFoundError


class GetProductUseCase(GetProductPort):
    def __init__(
        self,
        products: ProductRepositoryPort,
        categories: CategoryRepositoryPort,
        prices: PriceRepositoryPort,
    ) -> None:
        self._products = products
        self._categories = categories
        self._prices = prices

    def execute(self, product_id: str) -> ProductDetail:
        product = self._products.find_by_id(product_id)
        if product is None:
            raise ProductNotFoundError(product_id)

        category = self._categories.find_by_id(product.category_id)
        prices = self._prices.list_for_product(product_id)

        return ProductDetail(
            id=product.id,
            name=product.name,
            description=product.description,
            image_url=product.image_url,
            state=product.state.value,
            category_id=product.category_id,
            category=category,
            prices=prices,
        )