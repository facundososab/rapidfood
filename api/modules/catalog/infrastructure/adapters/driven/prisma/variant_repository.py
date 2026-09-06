from typing import Optional, List
from shared.infrastructure.prisma.db import db
from modules.catalog.application.ports.driven.variant_repository_port import VariantRepositoryPort
from modules.catalog.domain.models.product_variant import ProductVariant


class PrismaVariantRepository(VariantRepositoryPort):
    def save(self, variant: ProductVariant) -> ProductVariant:
        db.client.productvariant.upsert(
            where={"id": variant.id},
            data={
                "create": {
                    "id": variant.id,
                    "productId": variant.product_id,
                    "name": variant.name,
                    "available": variant.available,
                },
                "update": {
                    "name": variant.name,
                    "available": variant.available,
                },
            },
        )
        return variant

    def find_by_id(self, variant_id: str) -> Optional[ProductVariant]:
        record = db.client.productvariant.find_unique(where={"id": variant_id})
        return self._to_domain(record) if record else None

    def list_for_product(self, product_id: str) -> List[ProductVariant]:
        records = db.client.productvariant.find_many(where={"productId": product_id})
        return [self._to_domain(r) for r in records]

    def delete(self, variant_id: str) -> None:
        db.client.productvariant.delete(where={"id": variant_id})

    @staticmethod
    def _to_domain(record) -> ProductVariant:
        return ProductVariant(
            id=record.id,
            product_id=record.productId,
            name=record.name,
            available=record.available,
        )
