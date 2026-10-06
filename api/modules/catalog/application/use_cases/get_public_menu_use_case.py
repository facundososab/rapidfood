from __future__ import annotations

from modules.catalog.application.ports.driver.get_public_menu_ports import (
    GetPublicMenuPort,
    PublicCategory,
    PublicMenu,
    PublicModifierGroup,
    PublicModifierOption,
    PublicProduct,
    PublicVariant,
)
from modules.catalog.application.ports.driver.list_products_ports import (
    ListProductsQuery,
)
from modules.catalog.domain.models.product import ProductState


class GetPublicMenuUseCase(GetPublicMenuPort):
    def __init__(self, list_categories, list_products, product_query) -> None:
        self._list_categories = list_categories
        self._list_products = list_products
        self._product_query = product_query

    def execute(self) -> PublicMenu:
        categories = self._list_categories.execute()
        summaries = self._list_products.execute(
            ListProductsQuery(state=ProductState.AVAILABLE)
        )

        products_by_category = {category.id: [] for category in categories}
        orphans = []

        for summary in summaries:
            snapshot = self._product_query.find_product(summary.id)

            if snapshot is None:
                variants = ()
                modifier_groups = ()
            else:
                variants = tuple(
                    PublicVariant(
                        id=v.variant_id,
                        name=v.variant_name,
                        price=str(v.price) if v.price is not None else None,
                        available=v.is_available,
                    )
                    for v in snapshot.variants
                )
                modifier_groups = tuple(
                    PublicModifierGroup(
                        id=g.group_id,
                        name=g.name,
                        min_selections=g.min_selections,
                        max_selections=g.max_selections,
                        options=tuple(
                            PublicModifierOption(
                                id=o.option_id,
                                name=o.name,
                                price_delta=str(o.price_delta),
                                available=o.available,
                            )
                            for o in g.options
                        ),
                    )
                    for g in snapshot.modifier_groups
                )

            product = PublicProduct(
                id=summary.id,
                name=summary.name,
                description=summary.description,
                image_url=summary.image_url,
                variants=variants,
                modifier_groups=modifier_groups,
            )

            if summary.category_id in products_by_category:
                products_by_category[summary.category_id].append(product)
            else:
                orphans.append(product)

        menu_categories = [
            PublicCategory(
                id=category.id,
                name=category.description,
                products=tuple(products_by_category[category.id]),
            )
            for category in categories
        ]

        if orphans:
            menu_categories.append(
                PublicCategory(id="otros", name="Otros", products=tuple(orphans))
            )

        return PublicMenu(categories=tuple(menu_categories))
