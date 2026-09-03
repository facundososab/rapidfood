import pytest

from modules.catalog.application.ports.driver.delete_product_ports import (
    DeleteProductCommand,
)
from modules.catalog.application.use_cases.delete_product_use_case import (
    DeleteProductUseCase,
)
from modules.catalog.domain.errors.catalog_errors import (
    ProductInUseError,
    ProductNotFoundError,
)
from modules.catalog.domain.models.product import Product, ProductState


class FakeProductRepo:
    def __init__(self, products=None):
        self._products = products or {}

    def save(self, product):
        self._products[product.id] = product

    def find_by_id(self, product_id):
        return self._products.get(product_id)

    def list(self, category_id=None, state=None):
        return list(self._products.values())

    def delete(self, product_id):
        raise ProductInUseError(product_id)


class DeletingFakeProductRepo(FakeProductRepo):
    def delete(self, product_id):
        self._products.pop(product_id, None)


def _use_case(repo):
    return DeleteProductUseCase(products=repo)


def test_delete_product_removes_it():
    repo = DeletingFakeProductRepo({
        "p-1": Product(id="p-1", name="Pizza", description="Pizza",
                       state=ProductState.AVAILABLE, category_id="c-1"),
    })
    result = _use_case(repo).execute(DeleteProductCommand(product_id="p-1"))

    assert result.id == "p-1"
    assert repo.find_by_id("p-1") is None


def test_delete_missing_product_raises_not_found():
    with pytest.raises(ProductNotFoundError):
        _use_case(DeletingFakeProductRepo()).execute(DeleteProductCommand(product_id="p-1"))


def test_delete_product_in_use_propagates_error():
    repo = FakeProductRepo({
        "p-1": Product(id="p-1", name="Pizza", description="Pizza",
                       state=ProductState.AVAILABLE, category_id="c-1"),
    })
    with pytest.raises(ProductInUseError):
        _use_case(repo).execute(DeleteProductCommand(product_id="p-1"))