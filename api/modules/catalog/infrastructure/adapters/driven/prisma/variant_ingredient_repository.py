import uuid
from typing import List
from shared.infrastructure.prisma.db import db
from modules.catalog.application.ports.driven.variant_ingredient_repository_port import VariantIngredientRepositoryPort
from modules.catalog.domain.models.variant_ingredient import VariantIngredient


class PrismaVariantIngredientRepository(VariantIngredientRepositoryPort):
    def set_ingredients(self, variant_id: str, entries: List[dict]) -> List[VariantIngredient]:
        """Atomically replace all ingredients for a variant."""
        with db.client.tx() as tx:
            tx.productvariantingredient.delete_many(where={"productVariantId": variant_id})
            for entry in entries:
                tx.productvariantingredient.create(
                    data={
                        "id": str(uuid.uuid4()),
                        "productVariantId": variant_id,
                        "ingredientId": entry["ingredient_id"],
                        "removable": entry["removable"],
                    }
                )
        return self.list_for_variant(variant_id)

    def list_for_variant(self, variant_id: str) -> List[VariantIngredient]:
        records = db.client.productvariantingredient.find_many(
            where={"productVariantId": variant_id},
            include={"ingredient": True},
        )
        return [
            VariantIngredient(
                id=r.id,
                product_variant_id=r.productVariantId,
                ingredient_id=r.ingredientId,
                ingredient_name=r.ingredient.name,
                removable=r.removable,
            )
            for r in records
        ]
