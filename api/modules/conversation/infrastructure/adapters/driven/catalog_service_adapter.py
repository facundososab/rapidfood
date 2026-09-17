"""Adapts the catalog module's public query ports to `CatalogServicePort`.

Cross-context boundary: only the sibling's `application.ports` are imported
(enforced by import-linter) and the returned data is mapped into
conversation-owned DTOs. No Prisma models or catalog internals leak.
"""
from __future__ import annotations

from typing import Any, Optional

from modules.catalog.application.ports.driver.list_products_ports import (
    ListProductsQuery,
)
from modules.conversation.application.ports.driven.catalog_service import (
    CatalogServicePort,
    IngredientDTO,
    ModifierGroupDTO,
    ModifierOptionDTO,
    ProductDetailDTO,
    ProductSummaryDTO,
    ProductVariantPriceDTO,
    VariantDTO,
)

# The public ProductSummary DTO exposes availability as a plain string; using it
# keeps this adapter from importing the catalog domain model.
_AVAILABLE_STATE = "available"


class CatalogServiceAdapter(CatalogServicePort):
    def __init__(
        self,
        list_products: Any,
        product_query: Any,
        get_product: Any,
    ) -> None:
        self._list_products = list_products
        self._product_query = product_query
        self._get_product = get_product

    def search_products(
        self,
        business_configuration_id: str,
        query: Optional[str] = None,
        category_id: Optional[str] = None,
        only_available: bool = True,
    ) -> list[ProductSummaryDTO]:
        summaries = self._list_products.execute(
            ListProductsQuery(category_id=category_id, search=query)
        )
        return [
            ProductSummaryDTO(
                id=s.id,
                name=s.name,
                description=s.description,
                available=s.state == _AVAILABLE_STATE,
                category_id=s.category_id,
                # Variants + prices travel with the search result so the agent can
                # quote each option without a detail call per product.
                variants=self._variants_for(s.id),
            )
            for s in summaries
            if not only_available or s.state == _AVAILABLE_STATE
        ]

    def _variants_for(self, product_id: str):
        snapshot = self._product_query.find_product(product_id)
        if snapshot is None:
            return ()
        return tuple(
            ProductVariantPriceDTO(
                id=v.variant_id,
                name=v.variant_name,
                price=str(v.price) if v.price is not None else None,
                available=v.is_available,
            )
            for v in snapshot.variants
        )

    def get_product_detail(
        self, business_configuration_id: str, product_id: str
    ) -> Optional[ProductDetailDTO]:
        snapshot = self._product_query.find_product(product_id)
        if snapshot is None:
            return None

        description = snapshot.name
        try:
            detail = self._get_product.execute(product_id)
            description = getattr(detail, "description", description)
        except Exception:
            # Description is a nice-to-have; never fail the whole detail for it.
            pass

        return ProductDetailDTO(
            id=snapshot.product_id,
            name=snapshot.name,
            description=description,
            available=snapshot.is_available,
            variants=tuple(
                VariantDTO(
                    id=v.variant_id,
                    name=v.variant_name,
                    current_price=str(v.price) if v.price is not None else None,
                    available=v.is_available,
                    ingredients=tuple(
                        IngredientDTO(
                            id=i.ingredient_id, name=i.name, removable=i.removable
                        )
                        for i in v.ingredients
                    ),
                )
                for v in snapshot.variants
            ),
            modifier_groups=tuple(
                ModifierGroupDTO(
                    id=g.group_id,
                    name=g.name,
                    min_selections=g.min_selections,
                    max_selections=g.max_selections,
                    options=tuple(
                        ModifierOptionDTO(
                            id=o.option_id,
                            name=o.name,
                            price_delta=str(o.price_delta),
                            available=o.available,
                        )
                        for o in g.options
                    ),
                )
                for g in snapshot.modifier_groups
            ),
        )
