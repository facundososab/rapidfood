from modules.catalog.application.ports.driver.product_ports import(
    SetProductStateCommand,
    SetProductStatePort,
    SetProductStateResponse,
)
from modules.catalog.application.ports.driven.product_repository_port import(
    ProductRepositoryPort,
)
from modules.catalog.domain.errors.catalog_errors import ProductNotFoundError
from modules.catalog.domain.models.product import ProductState


class SetProductStateUseCase(SetProductStatePort):
    def __init__(self, products: ProductRepositoryPort) -> None:
        self.products = products

    def execute(self, command: SetProductStateCommand) -> SetProductStateResponse:
        product = self._products.find_by_id(command.product_id)
        if product is None:
            raise ProductNotFoundError(command.product_id)

        if command.state == ProductState.AVAILABLE:
            product.mark_available()
        else:
            product.mark_unavailable()

        self._products.save(product)

        return SetProductStateResponse(id=product.id, state=product.state.value)

    