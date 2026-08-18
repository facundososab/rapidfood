from modules.catalog.application.ports.driven.product_repository_port import (
    ProductRepositoryPort,
)
from modules.catalog.domain.models.product import Product, ProductState
from shared.infrastructure.prisma.db import db

class PrismaProductRepository(ProductRepositoryPort):
    def save(self, product: Product) -> None:
        db.client.product.upsert(
            where={"id": product.id},
            data={
                "create": {
                    "id": product.id,
                    "description": product.description,
                    "available": product.state == ProductState.AVAILABLE,
                    "categoryId": product.category_id,
                },
                "update": {
                    "description": product.description,
                    "available": product.state == ProductState.AVAILABLE,
                },
            },
        )

    def find_by_id(self, product_id: str) -> Product | None:
        record = db.client.product.find_unique(where={"id": product_id})
        if record is None:
            return None
        return self._to_domain(record)

    def list(
            self,
            category_id: str | None = None,
            state: ProductState | None = None,
    ) -> list[Product]:
        where: dict = {}
        if category_id is not None:
            where["categoryId"] = category_id
        if state is not None:
            where["available"] = state == ProductState.AVAILABLE

        records = db.client.product.find_many(where=where)
        return [self._to_domain(record) for record in records]


    @staticmethod
    def _to_domain(record) -> Product:
        return Product(
            id=record.id,
            description=record.description,
            state=ProductState.AVAILABLE if record.available else ProductState.UNAVAILABLE,
            category_id=record.categoryId,
        )