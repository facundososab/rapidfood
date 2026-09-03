from modules.catalog.application.ports.driver.set_discount_ports import (
    SetDiscountCommand,
    SetDiscountPort,
    SetDiscountResponse,
)
from modules.catalog.application.ports.driven.discount_repository_port import (
    DiscountRepositoryPort,
)
from modules.catalog.application.ports.driven.id_generator_port import IdGeneratorPort
from modules.catalog.application.ports.driven.product_repository_port import (
    ProductRepositoryPort,
)
from modules.catalog.domain.errors.catalog_errors import ProductNotFoundError
from modules.catalog.domain.models.discount import Discount


class SetDiscountUseCase(SetDiscountPort):
    def __init__(
            self,
            discounts: DiscountRepositoryPort,
            products: ProductRepositoryPort,
            id_generator: IdGeneratorPort,
    ) -> None:
        self._discounts = discounts
        self._products = products
        self._id_generator = id_generator


    def execute(self, command: SetDiscountCommand) -> SetDiscountResponse:
        if command.product_id is not None:
            if self._products.find_by_id(command.product_id) is None:
                raise ProductNotFoundError(command.product_id)

        discount = Discount(
            id=self._id_generator.generate(),
            percentage=command.percentage,
            product_id=command.product_id,
        )
        self._discounts.save(discount)

        return SetDiscountResponse(
            id=discount.id,
            percentage=discount.percentage,
            product_id=discount.product_id,
        )