import io
import logging
import os

import cloudinary
import cloudinary.uploader
from cloudinary.exceptions import Error as CloudinaryError

from modules.catalog.application.ports.driven.image_storage_port import (
    ImageStorageError,
    ImageStoragePort,
    StoredImage,
)

logger = logging.getLogger(__name__)


def _configure_cloudinary() -> None:
    cloudinary.config(
        cloud_name=os.environ["CLOUDINARY_CLOUD_NAME"],
        api_key=os.environ["CLOUDINARY_API_KEY"],
        api_secret=os.environ["CLOUDINARY_API_SECRET"],
        secure=True,
    )


class CloudinaryImageStorageAdapter(ImageStoragePort):
    """Driven adapter: uploads images to Cloudinary and returns the secure URL.

    Cloudinary is configured lazily on the first call so that the server can
    start even when CLOUDINARY_* env vars are not set (e.g. in local dev
    environments that never use image upload). Uploads are deterministic per
    ``public_id`` and overwrite in place, so replacing a product image does not
    accumulate orphaned assets.
    """

    def __init__(self, folder: str = "rapidfood/products") -> None:
        self._folder = folder
        self._configured = False

    def _ensure_configured(self) -> None:
        if self._configured:
            return
        try:
            _configure_cloudinary()
        except KeyError as exc:
            logger.error("Cloudinary is not configured: missing %s", exc)
            raise ImageStorageError(
                "El servicio de almacenamiento de imagenes no esta configurado."
            ) from exc
        self._configured = True

    def upload(self, file_data: bytes, filename: str, public_id: str) -> StoredImage:
        self._ensure_configured()
        try:
            result = cloudinary.uploader.upload(
                io.BytesIO(file_data),
                filename=filename,
                folder=self._folder,
                public_id=public_id,
                resource_type="image",
                overwrite=True,
                invalidate=True,
            )
        except CloudinaryError as exc:
            logger.exception("Cloudinary upload failed for public_id %s", public_id)
            raise ImageStorageError(
                "No se pudo subir la imagen al almacenamiento."
            ) from exc

        return StoredImage(url=result["secure_url"], public_id=result["public_id"])

    def delete(self, public_id: str) -> None:
        self._ensure_configured()
        try:
            cloudinary.uploader.destroy(public_id, invalidate=True)
        except CloudinaryError:
            logger.warning(
                "Cloudinary cleanup failed for public_id %s", public_id, exc_info=True
            )
