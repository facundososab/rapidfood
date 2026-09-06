from datetime import date

from modules.catalog.application.ports.driver.set_variant_price_ports import (
    SetVariantPricePort, SetVariantPriceCommand, SetVariantPriceResponse,
)
from modules.catalog.application.ports.driven.variant_repository_port import VariantRepositoryPort
from modules.catalog.application.ports.driven.price_repository_port import PriceRepositoryPort
from modules.catalog.application.ports.driven.id_generator_port import IdGeneratorPort
from modules.catalog.domain.models.price import Price
from modules.catalog.domain.errors.catalog_errors import VariantNotFoundError


class SetVariantPriceUseCase(SetVariantPricePort):
    def __init__(
        self,
        variant_repo: VariantRepositoryPort,
        price_repo: PriceRepositoryPort,
        id_generator: IdGeneratorPort,
    ) -> None:
        self._variant_repo = variant_repo
        self._price_repo = price_repo
        self._id_generator = id_generator

    def execute(self, command: SetVariantPriceCommand) -> SetVariantPriceResponse:
        variant = self._variant_repo.find_by_id(command.product_variant_id)
        if variant is None:
            raise VariantNotFoundError(command.product_variant_id)

        since_date = command.since_date or date.today()
        price = Price(
            id=self._id_generator.generate(),
            product_variant_id=variant.id,
            since_date=since_date,
            price=command.price,
        )
        self._price_repo.add(price)

        return SetVariantPriceResponse(
            price_id=price.id,
            product_variant_id=variant.id,
            price=command.price,
            since_date=since_date,
        )
