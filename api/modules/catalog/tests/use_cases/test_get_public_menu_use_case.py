"""Public menu use case: read model -> public categories/products/variants."""
from decimal import Decimal

from modules.catalog.application.ports.driven.public_menu_read_port import (
    MenuReadCategory,
    MenuReadModifierGroup,
    MenuReadModifierOption,
    MenuReadProduct,
    MenuReadVariant,
    PublicMenuReadModel,
)
from modules.catalog.application.use_cases.get_public_menu_use_case import (
    GetPublicMenuUseCase,
)


class FakeMenuReader:
    def __init__(self, read_model):
        self._read_model = read_model

    def load_available_menu(self):
        return self._read_model


def _product(product_id, category_id="cat-1", variants=(), modifier_groups=()):
    return MenuReadProduct(
        id=product_id,
        name=f"Product {product_id}",
        description="desc",
        image_url=None,
        category_id=category_id,
        variants=tuple(variants),
        modifier_groups=tuple(modifier_groups),
    )


def _use_case(categories=(), products=()):
    return GetPublicMenuUseCase(
        FakeMenuReader(
            PublicMenuReadModel(
                categories=tuple(categories), products=tuple(products)
            )
        )
    )


def test_variants_carry_string_price_and_availability():
    product = _product(
        "p-1",
        variants=(
            MenuReadVariant(
                id="v-1", name="Grande", price=Decimal("150.00"), available=True
            ),
            MenuReadVariant(id="v-2", name="Chica", price=None, available=False),
        ),
    )
    use_case = _use_case([MenuReadCategory(id="cat-1", name="Bebidas")], [product])

    menu = use_case.execute()

    variants = menu.categories[0].products[0].variants
    assert variants[0].id == "v-1"
    assert variants[0].name == "Grande"
    assert variants[0].price == "150.00"
    assert variants[0].available is True
    assert variants[1].price is None
    assert variants[1].available is False


def test_modifier_options_map_price_delta_as_string():
    product = _product(
        "p-1",
        modifier_groups=(
            MenuReadModifierGroup(
                id="g-1",
                name="Adiciones",
                min_selections=0,
                max_selections=3,
                options=(
                    MenuReadModifierOption(
                        id="o-1",
                        name="Extra queso",
                        price_delta=Decimal("50.00"),
                        available=True,
                    ),
                ),
            ),
        ),
    )
    use_case = _use_case([MenuReadCategory(id="cat-1", name="Bebidas")], [product])

    group = use_case.execute().categories[0].products[0].modifier_groups[0]

    assert group.id == "g-1"
    assert group.name == "Adiciones"
    assert group.min_selections == 0
    assert group.max_selections == 3
    assert group.options[0].id == "o-1"
    assert group.options[0].price_delta == "50.00"
    assert group.options[0].available is True


def test_products_are_grouped_by_category_in_port_order():
    use_case = _use_case(
        [
            MenuReadCategory(id="cat-1", name="Bebidas"),
            MenuReadCategory(id="cat-2", name="Platos"),
        ],
        [_product("p-2", category_id="cat-2"), _product("p-1", category_id="cat-1")],
    )

    menu = use_case.execute()

    assert [category.id for category in menu.categories] == ["cat-1", "cat-2"]
    assert [product.id for product in menu.categories[0].products] == ["p-1"]
    assert [product.id for product in menu.categories[1].products] == ["p-2"]


def test_orphan_product_lands_in_otros():
    use_case = _use_case(
        [MenuReadCategory(id="cat-1", name="Bebidas")],
        [_product("p-1", category_id="unknown")],
    )

    menu = use_case.execute()

    assert len(menu.categories) == 2
    assert menu.categories[0].id == "cat-1"
    assert menu.categories[1].id == "otros"
    assert menu.categories[1].name == "Otros"
    assert menu.categories[1].products[0].id == "p-1"


def test_product_without_variants_or_groups_is_still_listed():
    use_case = _use_case(
        [MenuReadCategory(id="cat-1", name="Bebidas")], [_product("p-1")]
    )

    product = use_case.execute().categories[0].products[0]

    assert product.variants == ()
    assert product.modifier_groups == ()


def test_no_orphans_means_no_otros_category():
    use_case = _use_case(
        [MenuReadCategory(id="cat-1", name="Bebidas")],
        [_product("p-1", category_id="cat-1")],
    )

    menu = use_case.execute()

    assert [category.id for category in menu.categories] == ["cat-1"]
