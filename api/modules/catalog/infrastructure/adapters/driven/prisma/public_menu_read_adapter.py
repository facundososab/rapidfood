"""Prisma read adapter for the public digital menu.

Loads categories, available products, their variants and modifier groups in a
constant number of queries (no per-product fan-out), then resolves each variant's
current price in memory. Kept in infrastructure so the application layer never
touches Prisma.
"""
from __future__ import annotations

from datetime import date, datetime
from decimal import Decimal
from typing import Any, Dict, List

from modules.catalog.application.ports.driven.public_menu_read_port import (
    MenuReadCategory,
    MenuReadModifierGroup,
    MenuReadModifierOption,
    MenuReadProduct,
    MenuReadVariant,
    PublicMenuReadModel,
    PublicMenuReaderPort,
)
from shared.infrastructure.prisma.db import db


class PrismaPublicMenuReadAdapter(PublicMenuReaderPort):
    def __init__(self, client: Any = None) -> None:
        self._client = client

    @property
    def _db(self):
        if self._client is not None:
            return self._client
        return db.client

    def load_available_menu(self) -> PublicMenuReadModel:
        categories = self._db.category.find_many()
        products = self._db.product.find_many(
            where={"available": True},
            include={"variants": True, "modifierGroups": True},
        )

        variant_ids = [variant.id for product in products for variant in product.variants]
        group_ids = [
            group.id for product in products for group in product.modifierGroups
        ]

        current_prices = self._current_prices_by_variant(variant_ids)
        options_by_group = self._options_by_group(group_ids)

        return PublicMenuReadModel(
            categories=tuple(
                MenuReadCategory(id=category.id, name=category.description)
                for category in categories
            ),
            products=tuple(
                self._to_product(product, current_prices, options_by_group)
                for product in products
            ),
        )

    def _current_prices_by_variant(
        self, variant_ids: List[str]
    ) -> Dict[str, Decimal]:
        if not variant_ids:
            return {}
        today = datetime.combine(date.today(), datetime.min.time())
        rows = self._db.price.find_many(
            where={
                "productVariantId": {"in": variant_ids},
                "sinceDate": {"lte": today},
            },
            order={"sinceDate": "desc"},
        )
        prices: Dict[str, Decimal] = {}
        for row in rows:
            # Ordered desc by sinceDate: the first row seen per variant is current.
            prices.setdefault(row.productVariantId, Decimal(str(row.price)))
        return prices

    def _options_by_group(
        self, group_ids: List[str]
    ) -> Dict[str, List[MenuReadModifierOption]]:
        if not group_ids:
            return {}
        rows = self._db.modifieroption.find_many(
            where={"modifierGroupId": {"in": group_ids}}
        )
        grouped: Dict[str, List[MenuReadModifierOption]] = {}
        for row in rows:
            grouped.setdefault(row.modifierGroupId, []).append(
                MenuReadModifierOption(
                    id=row.id,
                    name=row.name,
                    price_delta=Decimal(str(row.priceDelta)),
                    available=bool(row.available),
                )
            )
        return grouped

    @staticmethod
    def _to_product(
        product: Any,
        current_prices: Dict[str, Decimal],
        options_by_group: Dict[str, List[MenuReadModifierOption]],
    ) -> MenuReadProduct:
        return MenuReadProduct(
            id=product.id,
            name=product.name,
            description=product.description,
            image_url=product.imageUrl,
            category_id=product.categoryId,
            variants=tuple(
                MenuReadVariant(
                    id=variant.id,
                    name=variant.name,
                    price=current_prices.get(variant.id),
                    available=bool(variant.available),
                )
                for variant in product.variants
            ),
            modifier_groups=tuple(
                MenuReadModifierGroup(
                    id=group.id,
                    name=group.name,
                    min_selections=group.minSelections,
                    max_selections=group.maxSelections,
                    options=tuple(options_by_group.get(group.id, ())),
                )
                for group in product.modifierGroups
            ),
        )
