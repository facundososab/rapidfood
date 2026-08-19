from modules.catalog.application.ports.driver.get_product_ports import ProductDetail
from modules.catalog.application.ports.driver.update_product_ports import (
    UpdateProductCommand,
    UpdateProductPort,
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
from modules.catalog.domain.errors.catalog_errors import (
    CategoryNotFoundError,
    ProductNotFoundError,
)


class UpdateProductUseCase(UpdateProductPort):
    def __init__(
        self,
        products: ProductRepositoryPort,
        categories: CategoryRepositoryPort,
        prices: PriceRepositoryPort,
    ) -> None:
        self._products = products
        self._categories = categories
        self._prices = prices

    def execute(self, command: UpdateProductCommand) -> ProductDetail:
        product = self._products.find_by_id(command.product_id)
        if product is None:
            raise ProductNotFoundError(command.product_id)

        if command.name is not None:
            product.name = command.name

        if command.description is not None:
            product.description = command.description

        if command.image_url is not None:
            product.image_url = command.image_url or None

        if command.category_id is not None and command.category_id != product.category_id:
            if self._categories.find_by_id(command.category_id) is None:
                raise CategoryNotFoundError(command.category_id)
            product.category_id = command.category_id

        if command.available is not None:
            if command.available:
                product.mark_available()
            else:
                product.mark_unavailable()

        self._products.save(product)

        category = self._categories.find_by_id(product.category_id)
        prices = self._prices.list_for_product(product.id)

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