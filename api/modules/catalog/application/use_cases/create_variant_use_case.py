import uuid
from datetime import date
from decimal import Decimal

from modules.catalog.application.ports.driver.create_variant_ports import (
    CreateVariantPort, CreateVariantCommand, CreateVariantResponse,
)
from modules.catalog.application.ports.driven.variant_repository_port import VariantRepositoryPort
from modules.catalog.application.ports.driven.price_repository_port import PriceRepositoryPort
from modules.catalog.application.ports.driven.product_repository_port import ProductRepositoryPort
from modules.catalog.application.ports.driven.id_generator_port import IdGeneratorPort
from modules.catalog.domain.models.product_variant import ProductVariant
from modules.catalog.domain.models.price import Price
from modules.catalog.domain.errors.catalog_errors import ProductNotFoundError


class CreateVariantUseCase(CreateVariantPort):
    def __init__(
        self,
        product_repo: ProductRepositoryPort,
        variant_repo: VariantRepositoryPort,
        price_repo: PriceRepositoryPort,
        id_generator: IdGeneratorPort,
    ) -> None:
        self._product_repo = product_repo
        self._variant_repo = variant_repo
        self._price_repo = price_repo
        self._id_generator = id_generator

    def execute(self, command: CreateVariantCommand) -> CreateVariantResponse:
        product = self._product_repo.find_by_id(command.product_id)
        if product is None:
            raise ProductNotFoundError(command.product_id)

        variant = ProductVariant(
            id=self._id_generator.generate(),
            product_id=command.product_id,
            name=command.name,
            available=True,
        )
        self._variant_repo.save(variant)

        since_date = command.price_since_date or date.today()
        price = Price(
            id=self._id_generator.generate(),
            product_variant_id=variant.id,
            since_date=since_date,
            price=command.initial_price,
        )
        self._price_repo.add(price)

        return CreateVariantResponse(
            id=variant.id,
            product_id=variant.product_id,
            name=variant.name,
            available=variant.available,
            current_price=command.initial_price,
        )
