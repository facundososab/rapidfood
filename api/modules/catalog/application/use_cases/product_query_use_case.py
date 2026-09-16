from datetime import date
from typing import Optional

from modules.catalog.application.ports.driver.product_query_ports import (
    ProductQueryPort,
    ProductSnapshot,
    VariantSnapshot,
    IngredientSnapshot,
    ModifierGroupSnapshot,
    ModifierOptionSnapshot,
    VariantContext,
)
from modules.catalog.application.ports.driven.product_repository_port import ProductRepositoryPort
from modules.catalog.application.ports.driven.variant_repository_port import VariantRepositoryPort
from modules.catalog.application.ports.driven.price_repository_port import PriceRepositoryPort
from modules.catalog.application.ports.driven.variant_ingredient_repository_port import VariantIngredientRepositoryPort
from modules.catalog.application.ports.driven.modifier_repository_port import ModifierRepositoryPort


class ProductQueryUseCase(ProductQueryPort):
    def __init__(
        self,
        product_repo: ProductRepositoryPort,
        variant_repo: VariantRepositoryPort,
        price_repo: PriceRepositoryPort,
        variant_ingredient_repo: VariantIngredientRepositoryPort,
        modifier_repo: ModifierRepositoryPort,
    ) -> None:
        self._product_repo = product_repo
        self._variant_repo = variant_repo
        self._price_repo = price_repo
        self._variant_ingredient_repo = variant_ingredient_repo
        self._modifier_repo = modifier_repo

    def find_product(self, product_id: str) -> Optional[ProductSnapshot]:
        product = self._product_repo.find_by_id(product_id)
        if product is None:
            return None

        variants = self._variant_repo.list_for_product(product_id)
        modifier_groups = self._modifier_repo.list_groups_for_product(product_id)
        today = date.today()

        variant_snapshots = []
        for variant in variants:
            price = self._price_repo.find_current(variant.id, today)
            ingredients = self._variant_ingredient_repo.list_for_variant(variant.id)
            variant_snapshots.append(
                VariantSnapshot(
                    variant_id=variant.id,
                    variant_name=variant.name,
                    price=price.price if price else None,
                    is_available=product.available and variant.available,
                    ingredients=tuple(
                        IngredientSnapshot(
                            ingredient_id=vi.ingredient_id,
                            name=vi.ingredient_name,
                            removable=vi.removable,
                        )
                        for vi in ingredients
                    ),
                )
            )

        group_snapshots = []
        for group in modifier_groups:
            options = self._modifier_repo.list_options_for_group(group.id)
            group_snapshots.append(
                ModifierGroupSnapshot(
                    group_id=group.id,
                    name=group.name,
                    min_selections=group.min_selections,
                    max_selections=group.max_selections,
                    options=tuple(
                        ModifierOptionSnapshot(
                            option_id=opt.id,
                            name=opt.name,
                            price_delta=opt.price_delta,
                            available=opt.available,
                        )
                        for opt in options
                    ),
                )
            )

        return ProductSnapshot(
            product_id=product.id,
            name=product.name,
            is_available=product.available,
            variants=tuple(variant_snapshots),
            modifier_groups=tuple(group_snapshots),
        )

    def find_variant_context(self, variant_id: str) -> Optional[VariantContext]:
        from modules.catalog.application.ports.driven.variant_repository_port import VariantRepositoryPort

        variant = self._variant_repo.find_by_id(variant_id)
        if variant is None:
            return None

        product = self._product_repo.find_by_id(variant.product_id)
        if product is None:
            return None

        today = date.today()
        price = self._price_repo.find_current(variant.id, today)
        ingredients = self._variant_ingredient_repo.list_for_variant(variant.id)
        modifier_groups = self._modifier_repo.list_groups_for_product(product.id)

        from decimal import Decimal
        current_price = price.price if price else Decimal("0")

        group_snapshots = []
        for group in modifier_groups:
            options = self._modifier_repo.list_options_for_group(group.id)
            group_snapshots.append(
                ModifierGroupSnapshot(
                    group_id=group.id,
                    name=group.name,
                    min_selections=group.min_selections,
                    max_selections=group.max_selections,
                    options=tuple(
                        ModifierOptionSnapshot(
                            option_id=opt.id,
                            name=opt.name,
                            price_delta=opt.price_delta,
                            available=opt.available,
                        )
                        for opt in options
                    ),
                )
            )

        return VariantContext(
            product_id=product.id,
            product_name=product.name,
            product_available=product.available,
            variant_id=variant.id,
            variant_name=variant.name,
            variant_available=variant.available,
            current_price=current_price,
            ingredients=tuple(
                IngredientSnapshot(
                    ingredient_id=vi.ingredient_id,
                    name=vi.ingredient_name,
                    removable=vi.removable,
                )
                for vi in ingredients
            ),
            modifier_groups=tuple(group_snapshots),
        )
