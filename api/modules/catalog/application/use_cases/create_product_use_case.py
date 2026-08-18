from modules.catalog.application.ports.driver.product_ports import (
    CreateProductCommand,
    CreateProductPort,
    CreateProductResponse
)

from modules.catalog.application.ports.driven.category_repository_port import(
    CategoryRepositoryPort,
)
from modules.catalog.application.ports.driven.id_generator_port import IdGeneratorPort
from modules.catalog.application.ports.driven.product_repository_port import(
    ProductRepositoryPort,
)
from modules.catalog.domain.errors.catalog_errors import CategoryNotFoundError
from modules.catalog.domain.models.product import Product, ProductState


class CreateProductUseCase(CreateProductPort):
    def __init__(
            self,
            products: ProductRepositoryPort,
            categories: CategoryRepositoryPort,
            id_generator: IdGeneratorPort,
    ) -> None:
        self._products = products
        self._categories = categories
        self._id_generator = id_generator

    def execute(self, command: CreateProductCommand) -> CreateProductResponse:
        if self._categories.find_by_id(command.category_id) is None:
            raise CategoryNotFoundError(command.category_id)

        product = Product(
            id=self._id_generator.generate(),
            description=command.description,
            state=ProductState.UNAVAILABLE,
            category_id=command.category_id,
        )
        self._products.save(product)

        return CreateProductResponse(
            id=product.id,
            description=product.description,
            state=product.state.value,
            category_id=product.category_id
        )