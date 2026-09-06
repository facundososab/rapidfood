from typing import Optional, List
from shared.infrastructure.prisma.db import db
from modules.catalog.application.ports.driven.modifier_repository_port import ModifierRepositoryPort
from modules.catalog.domain.models.modifier_group import ModifierGroup
from modules.catalog.domain.models.modifier_option import ModifierOption
from decimal import Decimal


class PrismaModifierRepository(ModifierRepositoryPort):
    def save_group(self, group: ModifierGroup) -> ModifierGroup:
        db.client.modifiergroup.upsert(
            where={"id": group.id},
            data={
                "create": {
                    "id": group.id,
                    "productId": group.product_id,
                    "name": group.name,
                    "minSelections": group.min_selections,
                    "maxSelections": group.max_selections,
                },
                "update": {
                    "name": group.name,
                    "minSelections": group.min_selections,
                    "maxSelections": group.max_selections,
                },
            },
        )
        return group

    def find_group_by_id(self, group_id: str) -> Optional[ModifierGroup]:
        record = db.client.modifiergroup.find_unique(where={"id": group_id})
        if not record:
            return None
        return ModifierGroup(
            id=record.id,
            product_id=record.productId,
            name=record.name,
            min_selections=record.minSelections,
            max_selections=record.maxSelections,
        )

    def list_groups_for_product(self, product_id: str) -> List[ModifierGroup]:
        records = db.client.modifiergroup.find_many(where={"productId": product_id})
        return [
            ModifierGroup(
                id=r.id,
                product_id=r.productId,
                name=r.name,
                min_selections=r.minSelections,
                max_selections=r.maxSelections,
            )
            for r in records
        ]

    def delete_group(self, group_id: str) -> None:
        db.client.modifiergroup.delete(where={"id": group_id})

    def save_option(self, option: ModifierOption) -> ModifierOption:
        db.client.modifieroption.upsert(
            where={"id": option.id},
            data={
                "create": {
                    "id": option.id,
                    "modifierGroupId": option.modifier_group_id,
                    "name": option.name,
                    "priceDelta": option.price_delta,
                    "available": option.available,
                },
                "update": {
                    "name": option.name,
                    "priceDelta": option.price_delta,
                    "available": option.available,
                },
            },
        )
        return option

    def find_option_by_id(self, option_id: str) -> Optional[ModifierOption]:
        record = db.client.modifieroption.find_unique(where={"id": option_id})
        if not record:
            return None
        return ModifierOption(
            id=record.id,
            modifier_group_id=record.modifierGroupId,
            name=record.name,
            price_delta=Decimal(str(record.priceDelta)),
            available=record.available,
        )

    def list_options_for_group(self, group_id: str) -> List[ModifierOption]:
        records = db.client.modifieroption.find_many(where={"modifierGroupId": group_id})
        return [
            ModifierOption(
                id=r.id,
                modifier_group_id=r.modifierGroupId,
                name=r.name,
                price_delta=Decimal(str(r.priceDelta)),
                available=r.available,
            )
            for r in records
        ]

    def delete_option(self, option_id: str) -> None:
        db.client.modifieroption.delete(where={"id": option_id})
