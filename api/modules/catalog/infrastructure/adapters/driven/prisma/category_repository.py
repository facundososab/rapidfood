from modules.catalog.application.ports.driven.category_repository_port import (
    CategoryRepositoryPort,
)
from modules.catalog.domain.models.category import Category
from shared.infrastructure.prisma.db import db


class PrismaCategoryRepository(CategoryRepositoryPort):
    def save(self, category: Category) -> None:
        db.client.category.upsert(
            where={"id": category.id},
            data={
                "create": {
                    "id": category.id,
                    "description": category.description,
                },
                "update": {
                    "description": category.description,
                },
            },
        )

    def find_by_id(self, category_id: str) -> Category | None:
        record = db.client.category.find_unique(where={"id": category_id})
        if record is None:
            return None
        return self._to_domain(record)

    def list(self) -> list[Category]:
        records = db.client.category.find_many()
        return [self._to_domain(record) for record in records]

    @staticmethod
    def _to_domain(record) -> Category:
        return Category(id=record.id, description=record.description)
    