from datetime import date, datetime

from modules.catalog.application.ports.driven.price_repository_port import (
    PriceRepositoryPort,
)
from modules.catalog.domain.models.price import Price
from shared.infrastructure.prisma.db import db


class PrismaPriceRepository(PriceRepositoryPort):
    def add(self, price: Price) -> None:
        db.client.price.create(
            data={
                "id": price.id,
                "productVariantId": price.product_variant_id,
                "sinceDate": datetime.combine(price.since_date, datetime.min.time()),
                "price": price.price,
            }
        )

    def list_for_product(self, product_variant_id: str) -> list[Price]:
        records = db.client.price.find_many(
            where={"productVariantId": product_variant_id},
            order={"sinceDate": "desc"},
        )
        return [self._to_domain(record) for record in records]

    def find_current(self, product_variant_id: str, on_date: date) -> Price | None:
        records = db.client.price.find_many(
            where={
                "productVariantId": product_variant_id,
                "sinceDate": {"lte": datetime.combine(on_date, datetime.min.time())},
            },
            order={"sinceDate": "desc"},
            take=1,
        )
        if not records:
            return None
        return self._to_domain(records[0])
    @staticmethod
    def _to_domain(record) -> Price:
        return Price(
            id=record.id,
            product_variant_id=record.productVariantId,
            since_date=record.sinceDate.date(),
            price=record.price,
        )