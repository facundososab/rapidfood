from typing import Optional, List
from shared.infrastructure.prisma.db import db
from modules.catalog.application.ports.driven.ingredient_repository_port import IngredientRepositoryPort
from modules.catalog.domain.models.ingredient import Ingredient


class PrismaIngredientRepository(IngredientRepositoryPort):
    def save(self, ingredient: Ingredient) -> Ingredient:
        db.client.ingredient.upsert(
            where={"id": ingredient.id},
            data={
                "create": {"id": ingredient.id, "name": ingredient.name},
                "update": {"name": ingredient.name},
            },
        )
        return ingredient

    def find_by_id(self, ingredient_id: str) -> Optional[Ingredient]:
        record = db.client.ingredient.find_unique(where={"id": ingredient_id})
        return Ingredient(id=record.id, name=record.name) if record else None

    def list_all(self) -> List[Ingredient]:
        records = db.client.ingredient.find_many(order={"name": "asc"})
        return [Ingredient(id=r.id, name=r.name) for r in records]
