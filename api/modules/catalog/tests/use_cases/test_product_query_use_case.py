from datetime import date
from decimal import Decimal

from modules.catalog.application.use_cases.product_query_use_case import (
    ProductQueryUseCase,
)
from modules.catalog.domain.models.product_variant import ProductVariant
from modules.catalog.domain.models.price import Price


class FakeProduct:
    """Stub that exposes the interface expected by ProductQueryUseCase."""
    def __init__(self, id, name, available):
        self.id = id
        self.name = name
        self.available = available


class FakeProductRepo:
    def __init__(self, products=None):
        self._products = products or {}

    def save(self, product):
        self._products[product.id] = product

    def find_by_id(self, product_id):
        return self._products.get(product_id)

    def list(self, category_id=None, state=None):
        return list(self._products.values())


class FakeVariantRepo:
    def __init__(self, variants=None):
        # keyed by variant_id
        self._variants = variants or {}

    def save(self, variant):
        self._variants[variant.id] = variant
        return variant

    def find_by_id(self, variant_id):
        return self._variants.get(variant_id)

    def list_for_product(self, product_id):
        return [v for v in self._variants.values() if v.product_id == product_id]

    def delete(self, variant_id):
        self._variants.pop(variant_id, None)


class FakePriceRepo:
    def __init__(self, prices=None):
        # keyed by variant_id
        self._prices = prices or {}

    def find_current(self, variant_id, on_date):
        return self._prices.get(variant_id)


class FakeVariantIngredientRepo:
    def set_ingredients(self, variant_id, entries):
        return []

    def list_for_variant(self, variant_id):
        return []


class FakeModifierRepo:
    def save_group(self, group):
        return group

    def find_group_by_id(self, group_id):
        return None

    def list_groups_for_product(self, product_id):
        return []

    def delete_group(self, group_id):
        pass

    def save_option(self, option):
        return option

    def find_option_by_id(self, option_id):
        return None

    def list_options_for_group(self, group_id):
        return []

    def delete_option(self, option_id):
        pass


def _use_case(products=None, variants=None, prices=None):
    return ProductQueryUseCase(
        product_repo=FakeProductRepo(products),
        variant_repo=FakeVariantRepo(variants),
        price_repo=FakePriceRepo(prices),
        variant_ingredient_repo=FakeVariantIngredientRepo(),
        modifier_repo=FakeModifierRepo(),
    )


def test_find_product_returns_snapshot_when_available():
    product = FakeProduct(id="p-1", name="Pizza", available=True)
    variant = ProductVariant(id="v-1", product_id="p-1", name="Regular", available=True)
    price = Price(id="pr-1", product_variant_id="v-1", since_date=date.today(), price=Decimal("150.00"))

    use_case = _use_case(
        products={"p-1": product},
        variants={"v-1": variant},
        prices={"v-1": price},
    )

    snapshot = use_case.find_product("p-1")

    assert snapshot is not None
    assert snapshot.product_id == "p-1"
    assert snapshot.is_available is True
    assert len(snapshot.variants) == 1
    assert snapshot.variants[0].variant_id == "v-1"
    assert snapshot.variants[0].price == Decimal("150.00")


def test_find_product_returns_none_when_product_missing():
    use_case = _use_case()

    assert use_case.find_product("missing") is None


def test_find_product_returns_snapshot_with_no_current_price_as_none():
    """When no price is found for the variant, the variant snapshot has price=None."""
    product = FakeProduct(id="p-1", name="Pizza", available=True)
    variant = ProductVariant(id="v-1", product_id="p-1", name="Regular", available=True)

    use_case = _use_case(
        products={"p-1": product},
        variants={"v-1": variant},
        prices={},
    )

    snapshot = use_case.find_product("p-1")
    assert snapshot is not None
    assert len(snapshot.variants) == 1
    assert snapshot.variants[0].price is None


def test_find_product_marks_unavailable_product():
    product = FakeProduct(id="p-1", name="Pizza", available=False)
    variant = ProductVariant(id="v-1", product_id="p-1", name="Regular", available=True)
    price = Price(id="pr-1", product_variant_id="v-1", since_date=date.today(), price=Decimal("150.00"))

    use_case = _use_case(
        products={"p-1": product},
        variants={"v-1": variant},
        prices={"v-1": price},
    )

    snapshot = use_case.find_product("p-1")

    assert snapshot is not None
    assert snapshot.is_available is False
    # Variant is_available reflects product.available AND variant.available
    assert snapshot.variants[0].is_available is False
