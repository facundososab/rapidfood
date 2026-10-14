from modules.catalog.application.ports.driver.upload_product_image_ports import (
    UploadProductImageCommand,
    UploadProductImagePort,
    UploadProductImageResponse,
)
from modules.catalog.application.ports.driven.image_storage_port import ImageStoragePort
from modules.catalog.application.ports.driven.product_repository_port import (
    ProductRepositoryPort,
)
from modules.catalog.domain.errors.catalog_errors import ProductNotFoundError


class UploadProductImageUseCase(UploadProductImagePort):
    def __init__(
        self,
        products: ProductRepositoryPort,
        image_storage: ImageStoragePort,
    ) -> None:
        self._products = products
        self._image_storage = image_storage

    def execute(
        self, command: UploadProductImageCommand
    ) -> UploadProductImageResponse:
        product = self._products.find_by_id(command.product_id)
        if product is None:
            raise ProductNotFoundError(command.product_id)

        stored = self._image_storage.upload(
            file_data=command.file_data,
            filename=command.filename,
            public_id=command.product_id,
        )

        product.image_url = stored.url
        try:
            self._products.save(product)
        except Exception:
            self._image_storage.delete(stored.public_id)
            raise

        return UploadProductImageResponse(image_url=stored.url)
