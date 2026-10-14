from __future__ import annotations

from modules.catalog.application.ports.driven.public_menu_read_port import (
    PublicMenuReaderPort,
)
from modules.catalog.application.ports.driver.get_public_menu_ports import (
    GetPublicMenuPort,
    PublicCategory,
    PublicMenu,
    PublicModifierGroup,
    PublicModifierOption,
    PublicProduct,
    PublicVariant,
)

_ORPHAN_CATEGORY_ID = "otros"
_ORPHAN_CATEGORY_NAME = "Otros"


class GetPublicMenuUseCase(GetPublicMenuPort):
    """Assembles the public menu from a dedicated read model.

    Depends on a driven read port (not on sibling use cases), so it owns only the
    presentation rule — grouping products whose category is missing under
    "Otros" — and the current price is already resolved by the adapter.
    """

    def __init__(self, menu_reader: PublicMenuReaderPort) -> None:
        self._menu_reader = menu_reader

    def execute(self) -> PublicMenu:
        read_model = self._menu_reader.load_available_menu()

        products_by_category: dict[str, list[PublicProduct]] = {
            category.id: [] for category in read_model.categories
        }
        orphans: list[PublicProduct] = []

        for product in read_model.products:
            mapped = PublicProduct(
                id=product.id,
                name=product.name,
                description=product.description,
                image_url=product.image_url,
                variants=tuple(
                    PublicVariant(
                        id=variant.id,
                        name=variant.name,
                        price=(
                            str(variant.price) if variant.price is not None else None
                        ),
                        available=variant.available,
                    )
                    for variant in product.variants
                ),
                modifier_groups=tuple(
                    PublicModifierGroup(
                        id=group.id,
                        name=group.name,
                        min_selections=group.min_selections,
                        max_selections=group.max_selections,
                        options=tuple(
                            PublicModifierOption(
                                id=option.id,
                                name=option.name,
                                price_delta=str(option.price_delta),
                                available=option.available,
                            )
                            for option in group.options
                        ),
                    )
                    for group in product.modifier_groups
                ),
            )

            if product.category_id in products_by_category:
                products_by_category[product.category_id].append(mapped)
            else:
                orphans.append(mapped)

        menu_categories = [
            PublicCategory(
                id=category.id,
                name=category.name,
                products=tuple(products_by_category[category.id]),
            )
            for category in read_model.categories
        ]

        if orphans:
            menu_categories.append(
                PublicCategory(
                    id=_ORPHAN_CATEGORY_ID,
                    name=_ORPHAN_CATEGORY_NAME,
                    products=tuple(orphans),
                )
            )

        return PublicMenu(categories=tuple(menu_categories))
