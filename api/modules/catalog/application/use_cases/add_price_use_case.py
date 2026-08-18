from modules.catalog.application.ports.driver.add_price_ports import (
    AddPriceCommand,
    AddPricePort,
    AddPriceResponse,
)
from modules.catalog.application.ports.driven.id_generator_port import IdGeneratorPort
from modules.catalog.application.ports.driven.price_repository_port import (
    PriceRepositoryPort,
)
from modules.catalog.application.ports.driven.product_repository_port import (
    ProductRepositoryPort,
)
from modules.catalog.domain.errors.catalog_errors import ProductNotFoundError
from modules.catalog.domain.models.price import Price


class AddPriceUseCase(AddPricePort):
    def __init__(
            self,
            products: ProductRepositoryPort,
            prices: PriceRepositoryPort,
            id_generator: IdGeneratorPort,
    ) -> None:
        self._products = products
        self._prices = prices
        self._id_generator = id_generator

    def execute(self, command: AddPriceCommand) -> AddPriceResponse:
        if self._products.find_by_id(command.product_id) is None:
            raise ProductNotFoundError(command.product_id)

        price = Price(
            id=self._id_generator.generate(),
            product_id=command.product_id,
            since_date=command.since_date,
            price=command.price,
        )
        self._prices.add(price) #No save, no update, solo se agrega

        return AddPriceResponse(
            id=price.id,
            product_id=price.product_id,
            since_date=price.since_date,
            price=price.price,
        )