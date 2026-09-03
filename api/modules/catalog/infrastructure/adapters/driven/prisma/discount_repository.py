from modules.catalog.application.ports.driven.discount_repository_port import (
    DiscountRepositoryPort,
)
from modules.catalog.domain.models.discount import Discount
from shared.infrastructure.prisma.db import db


class PrismaDiscountRepository(DiscountRepositoryPort):
    def save(self, discount: Discount) -> None:
        db.client.discount.upsert(
            where={"id": discount.id},
            data={
                "create": {
                    "id": discount.id,
                    "percentage": discount.percentage,
                    "productId": discount.product_id,
                },
                "update": {
                    "percentage": discount.percentage,
                    "productId": discount.product_id,
                },
            },
        )


    def list_for_product(self, product_id: str) -> list[Discount]:
        records = db.client.discount.find_many(
            where={
                "OR": [
                    {"productId": product_id},
                    {"productId": None},
                ]
            }
        )
        return [self._to_domain(record) for record in records]

    @staticmethod
    def _to_domain(record) -> Discount:
        return Discount(
            id=record.id,
            percentage=record.percentage,
            product_id=record.productId,
        )