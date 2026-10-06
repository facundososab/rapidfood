"""Public menu use case: categories -> available products -> variants/modifiers."""
from decimal import Decimal

from modules.catalog.application.ports.driver.list_products_ports import ProductSummary
from modules.catalog.application.ports.driver.product_query_ports import (
    ModifierGroupSnapshot,
    ModifierOptionSnapshot,
    ProductSnapshot,
    VariantSnapshot,
)
from modules.catalog.application.use_cases.get_public_menu_use_case import (
    GetPublicMenuUseCase,
)
from modules.catalog.domain.models.category import Category
from modules.catalog.domain.models.product import ProductState


class FakeListCategories:
    def __init__(self, categories):
        self._categories = categories

    def execute(self):
        return list(self._categories)


class FakeListProducts:
    def __init__(self, summaries):
        self._summaries = summaries
        self.last_query = None

    def execute(self, query):
        self.last_query = query
        return list(self._summaries)


class FakeProductQuery:
    def __init__(self, snapshots):
        self._snapshots = snapshots

    def find_product(self, product_id):
        return self._snapshots.get(product_id)


def _summary(product_id, category_id="cat-1"):
    return ProductSummary(
        id=product_id,
        name=f"Product {product_id}",
        description="desc",
        image_url=None,
        state=ProductState.AVAILABLE.value,
        category_id=category_id,
    )


def _use_case(categories, summaries, snapshots=None):
    return GetPublicMenuUseCase(
        FakeListCategories(categories),
        FakeListProducts(summaries),
        FakeProductQuery(snapshots or {}),
    )


def test_only_available_products_are_requested():
    list_products = FakeListProducts([])
    use_case = GetPublicMenuUseCase(
        FakeListCategories([]), list_products, FakeProductQuery({})
    )

    use_case.execute()

    assert list_products.last_query.state == ProductState.AVAILABLE


def test_variants_carry_string_price_and_availability():
    snapshot = ProductSnapshot(
        product_id="p-1",
        name="Product p-1",
        is_available=True,
        variants=(
            VariantSnapshot(
                variant_id="v-1",
                variant_name="Grande",
                price=Decimal("150.00"),
                is_available=True,
            ),
            VariantSnapshot(
                variant_id="v-2",
                variant_name="Chica",
                price=None,
                is_available=False,
            ),
        ),
        modifier_groups=(),
    )
    use_case = _use_case(
        [Category(id="cat-1", description="Bebidas")],
        [_summary("p-1")],
        {"p-1": snapshot},
    )

    menu = use_case.execute()

    variants = menu.categories[0].products[0].variants
    assert variants[0].id == "v-1"
    assert variants[0].name == "Grande"
    assert variants[0].price == "150.00"
    assert variants[0].available is True
    assert variants[1].price is None
    assert variants[1].available is False


def test_modifier_options_map_price_delta_as_string():
    snapshot = ProductSnapshot(
        product_id="p-1",
        name="Product p-1",
        is_available=True,
        variants=(),
        modifier_groups=(
            ModifierGroupSnapshot(
                group_id="g-1",
                name="Adiciones",
                min_selections=0,
                max_selections=3,
                options=(
                    ModifierOptionSnapshot(
                        option_id="o-1",
                        name="Extra queso",
                        price_delta=Decimal("50.00"),
                        available=True,
                    ),
                ),
            ),
        ),
    )
    use_case = _use_case(
        [Category(id="cat-1", description="Bebidas")],
        [_summary("p-1")],
        {"p-1": snapshot},
    )

    group = use_case.execute().categories[0].products[0].modifier_groups[0]

    assert group.id == "g-1"
    assert group.name == "Adiciones"
    assert group.min_selections == 0
    assert group.max_selections == 3
    assert group.options[0].id == "o-1"
    assert group.options[0].price_delta == "50.00"
    assert group.options[0].available is True


def test_orphan_product_lands_in_otros():
    use_case = _use_case(
        [Category(id="cat-1", description="Bebidas")],
        [_summary("p-1", category_id="unknown")],
    )

    menu = use_case.execute()

    assert len(menu.categories) == 2
    assert menu.categories[0].id == "cat-1"
    assert menu.categories[1].id == "otros"
    assert menu.categories[1].name == "Otros"
    assert menu.categories[1].products[0].id == "p-1"


def test_product_without_snapshot_has_empty_variants_and_groups():
    use_case = _use_case(
        [Category(id="cat-1", description="Bebidas")],
        [_summary("p-1")],
    )

    product = use_case.execute().categories[0].products[0]

    assert product.variants == ()
    assert product.modifier_groups == ()
