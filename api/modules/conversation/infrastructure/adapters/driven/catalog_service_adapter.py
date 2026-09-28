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


def _tokens(query: Optional[str]) -> list[str]:
    """Lowercased search tokens; punctuation/separators are neutralized."""
    if not query:
        return []
    normalized = query.lower().replace("-", " ").replace(",", " ")
    return [token for token in normalized.split() if token]


def _matches(tokens: list[str], summary: Any, variants: tuple) -> bool:
    """True when EVERY token appears in the product name/description or a variant.

    All tokens must match ("Classic Burger Doble" needs both the product and the
    "Doble" variant), which is what lets the agent find a variant by its name.
    """
    haystack = " ".join(
        [
            (summary.name or ""),
            (summary.description or ""),
            *[(v.name or "") for v in variants],
        ]
    ).replace("-", " ").lower()
    return all(token in haystack for token in tokens)


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
        # Match in the conversation boundary, not in the DB: the agent searches
        # with human terms ("Coca-Cola 500", "Classic Burger Doble") that live in
        # the VARIANT name, and a naive `name/description contains <full string>`
        # misses them (and a free-form category id would blow up on a UUID
        # column). Fetch the menu and match token-by-token against product AND
        # variant names.
        summaries = self._list_products.execute(
            ListProductsQuery(category_id=category_id, search=None)
        )
        tokens = _tokens(query)
        results: list[ProductSummaryDTO] = []
        for summary in summaries:
            if only_available and summary.state != _AVAILABLE_STATE:
                continue
            variants = self._variants_for(summary.id)
            if tokens and not _matches(tokens, summary, variants):
                continue
            results.append(
                ProductSummaryDTO(
                    id=summary.id,
                    name=summary.name,
                    description=summary.description,
                    available=summary.state == _AVAILABLE_STATE,
                    category_id=summary.category_id,
                    # Variants + prices travel with the search result so the agent
                    # can quote each option without a detail call per product.
                    variants=variants,
                )
            )
        return results

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
