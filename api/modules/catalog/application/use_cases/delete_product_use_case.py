from modules.catalog.application.ports.driver.delete_product_ports import (
    DeleteProductCommand,
    DeleteProductPort,
    DeleteProductResponse,
)
from modules.catalog.application.ports.driven.product_repository_port import (
    ProductRepositoryPort,
)
from modules.catalog.domain.errors.catalog_errors import ProductNotFoundError


class DeleteProductUseCase(DeleteProductPort):
    def __init__(self, products: ProductRepositoryPort) -> None:
        self._products = products

    def execute(self, command: DeleteProductCommand) -> DeleteProductResponse:
        product = self._products.find_by_id(command.product_id)
        if product is None:
            raise ProductNotFoundError(command.product_id)

        self._products.delete(command.product_id)

        return DeleteProductResponse(id=command.product_id)