import pytest

from modules.catalog.application.ports.driven.image_storage_port import StoredImage
from modules.catalog.application.ports.driver.upload_product_image_ports import (
    UploadProductImageCommand,
)
from modules.catalog.application.use_cases.upload_product_image_use_case import (
    UploadProductImageUseCase,
)
from modules.catalog.domain.errors.catalog_errors import ProductNotFoundError
from modules.catalog.domain.models.product import Product, ProductState


class FakeProductRepository:
    def __init__(self, products=None):
        self._products = products or {}
        self.saved = []

    def find_by_id(self, product_id):
        return self._products.get(product_id)

    def save(self, product):
        self._products[product.id] = product
        self.saved.append(product)


class FailingSaveProductRepository(FakeProductRepository):
    def save(self, product):
        raise RuntimeError("database unavailable")


class FakeImageStorage:
    def __init__(self, url="https://cdn.example.com/image.jpg", public_id="img-1"):
        self._stored = StoredImage(url=url, public_id=public_id)
        self.uploads = []
        self.deleted = []

    def upload(self, file_data, filename, public_id):
        self.uploads.append((file_data, filename, public_id))
        return self._stored

    def delete(self, public_id):
        self.deleted.append(public_id)


def _product(product_id="p-1"):
    return Product(
        id=product_id,
        name="Pizza",
        description="Pizza",
        state=ProductState.AVAILABLE,
        category_id="c-1",
    )


def test_upload_persists_url_and_returns_response():
    repo = FakeProductRepository({"p-1": _product()})
    storage = FakeImageStorage(url="https://cdn.example.com/p1.jpg")
    use_case = UploadProductImageUseCase(repo, storage)

    result = use_case.execute(
        UploadProductImageCommand(
            product_id="p-1", file_data=b"bytes", filename="p1.jpg"
        )
    )

    assert result.image_url == "https://cdn.example.com/p1.jpg"
    assert repo.find_by_id("p-1").image_url == "https://cdn.example.com/p1.jpg"
    assert storage.uploads == [(b"bytes", "p1.jpg", "p-1")]


def test_upload_missing_product_raises_and_skips_storage():
    storage = FakeImageStorage()
    use_case = UploadProductImageUseCase(FakeProductRepository(), storage)

    with pytest.raises(ProductNotFoundError):
        use_case.execute(
            UploadProductImageCommand(
                product_id="missing", file_data=b"bytes", filename="x.jpg"
            )
        )

    assert storage.uploads == []


def test_failed_persistence_deletes_uploaded_asset():
    repo = FailingSaveProductRepository({"p-1": _product()})
    storage = FakeImageStorage(public_id="rapidfood/products/p-1")
    use_case = UploadProductImageUseCase(repo, storage)

    with pytest.raises(RuntimeError):
        use_case.execute(
            UploadProductImageCommand(
                product_id="p-1", file_data=b"bytes", filename="p1.jpg"
            )
        )

    assert storage.deleted == ["rapidfood/products/p-1"]
