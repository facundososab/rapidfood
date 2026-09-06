from modules.catalog.application.ports.driver.create_product_ports import (
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
from modules.catalog.application.ports.driven.variant_repository_port import VariantRepositoryPort
from modules.catalog.domain.errors.catalog_errors import CategoryNotFoundError
from modules.catalog.domain.models.product import Product, ProductState
from modules.catalog.domain.models.product_variant import ProductVariant


class CreateProductUseCase(CreateProductPort):
    def __init__(
            self,
            product_repo: ProductRepositoryPort,
            category_repo: CategoryRepositoryPort,
            id_generator: IdGeneratorPort,
            variant_repo: VariantRepositoryPort,
    ) -> None:
        self._products = product_repo
        self._categories = category_repo
        self._id_generator = id_generator
        self._variants = variant_repo

    def execute(self, command: CreateProductCommand) -> CreateProductResponse:
        if self._categories.find_by_id(command.category_id) is None:
            raise CategoryNotFoundError(command.category_id)

        product = Product(
            id=self._id_generator.generate(),
            name=command.name,
            description=command.description,
            image_url=command.image_url or None,
            state=ProductState.UNAVAILABLE,
            category_id=command.category_id,
        )
        self._products.save(product)
        
        variant = ProductVariant(
            id=self._id_generator.generate(),
            product_id=product.id,
            name="Default"
        )
        self._variants.save(variant)

        return CreateProductResponse(
            id=product.id,
            name=product.name,
            description=product.description,
            image_url=product.image_url,
            state=product.state.value,
            category_id=product.category_id
        )
