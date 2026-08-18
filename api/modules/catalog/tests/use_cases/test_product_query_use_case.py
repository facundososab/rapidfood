from datetime import date
from decimal import Decimal

from modules.catalog.application.use_cases.product_query_use_case import (
    ProductQueryUseCase,
)
from modules.catalog.domain.models.product import Product, ProductState
from modules.catalog.domain.models.price import Price


class FakeProductRepo:
    def __init__(self, products=None):
        self._products = products or {}

    def save(self, product):
        self._products[product.id] = product

    def find_by_id(self, product_id):
        return self._products.get(product_id)

    def list(self, category_id=None, state=None):
        return list(self._products.values())


class FakePriceRepo:
    def __init__(self, prices=None):
        self._prices = prices or {}

    def add(self, price):
        self._prices[price.product_id] = price

    def list_for_product(self, product_id):
        return [self._prices[product_id]] if product_id in self._prices else []

    def find_current(self, product_id, on_date):
        return self._prices.get(product_id)


def _use_case(products=None, prices=None):
    return ProductQueryUseCase(
        products=FakeProductRepo(products),
        prices=FakePriceRepo(prices),
    )


def test_find_product_returns_snapshot_when_available():
    product = Product(id="p-1", name="Pizza", description="Pizza", state=ProductState.AVAILABLE, category_id="c-1")
    price = Price(id="pr-1", product_id="p-1", since_date=date.today(), price=Decimal("150.00"))
    use_case = _use_case(products={"p-1": product}, prices={"p-1": price})

    snapshot = use_case.find_product("p-1")

    assert snapshot is not None
    assert snapshot.product_id == "p-1"
    assert snapshot.price == Decimal("150.00")
    assert snapshot.is_available is True


def test_find_product_returns_none_when_product_missing():
    use_case = _use_case()

    assert use_case.find_product("missing") is None


def test_find_product_returns_none_when_no_current_price():
    product = Product(id="p-1", name="Pizza", description="Pizza", state=ProductState.AVAILABLE, category_id="c-1")
    use_case = _use_case(products={"p-1": product})

    assert use_case.find_product("p-1") is None


def test_find_product_marks_unavailable_product():
    product = Product(id="p-1", name="Pizza", description="Pizza", state=ProductState.UNAVAILABLE, category_id="c-1")
    price = Price(id="pr-1", product_id="p-1", since_date=date.today(), price=Decimal("150.00"))
    use_case = _use_case(products={"p-1": product}, prices={"p-1": price})

    snapshot = use_case.find_product("p-1")

    assert snapshot is not None
    assert snapshot.is_available is False
