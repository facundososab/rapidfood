from typing import Optional
from decimal import Decimal

from modules.catalog.application.ports.driver.product_query_ports import (
    ProductQueryPort,
    VariantContext as CatalogVariantContext,
)
from modules.order.application.ports.driven.catalog_query import (
    CatalogQuery,
    VariantContext,
    IngredientInfo,
    ModifierGroupInfo,
    ModifierOptionInfo,
)


class CatalogProductQuery(CatalogQuery):
    """
    Adapts the catalog module's public query port to the order driven port.

    The order module depends only on modules.catalog.application.ports
    (enforced by import-linter). The concrete query is injected by the
    composition root.
    """

    def __init__(self, catalog_query: ProductQueryPort) -> None:
        self._catalog_query = catalog_query

    def get_variant_context(self, variant_id: str) -> Optional[VariantContext]:
        catalog_ctx = self._catalog_query.find_variant_context(variant_id)
        if catalog_ctx is None:
            return None

        return VariantContext(
            product_id=catalog_ctx.product_id,
            product_name=catalog_ctx.product_name,
            product_available=catalog_ctx.product_available,
            variant_id=catalog_ctx.variant_id,
            variant_name=catalog_ctx.variant_name,
            variant_available=catalog_ctx.variant_available,
            current_price=catalog_ctx.current_price,
            ingredients=tuple(
                IngredientInfo(
                    ingredient_id=ing.ingredient_id,
                    name=ing.name,
                    removable=ing.removable,
                )
                for ing in catalog_ctx.ingredients
            ),
            modifier_groups=tuple(
                ModifierGroupInfo(
                    group_id=g.group_id,
                    name=g.name,
                    min_selections=g.min_selections,
                    max_selections=g.max_selections,
                    options=tuple(
                        ModifierOptionInfo(
                            option_id=o.option_id,
                            name=o.name,
                            price_delta=o.price_delta,
                            available=o.available,
                        )
                        for o in g.options
                    ),
                )
                for g in catalog_ctx.modifier_groups
            ),
        )
