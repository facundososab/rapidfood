import io
import os

import cloudinary
import cloudinary.uploader

from modules.catalog.application.ports.driven.image_storage_port import ImageStoragePort


def _configure_cloudinary() -> None:
    cloudinary.config(
        cloud_name=os.environ["CLOUDINARY_CLOUD_NAME"],
        api_key=os.environ["CLOUDINARY_API_KEY"],
        api_secret=os.environ["CLOUDINARY_API_SECRET"],
        secure=True,
    )


class CloudinaryImageStorageAdapter(ImageStoragePort):
    """Driven adapter: uploads images to Cloudinary and returns the secure URL.

    Cloudinary is configured lazily on the first upload call so that the server
    can start even when CLOUDINARY_* env vars are not set (e.g. in local dev
    environments that never use image upload).
    """

    def __init__(self, folder: str = "rapidfood/products") -> None:
        self._folder = folder
        self._configured = False

    def _ensure_configured(self) -> None:
        if not self._configured:
            _configure_cloudinary()
            self._configured = True

    def upload(self, file_data: bytes, filename: str, content_type: str) -> str:
        self._ensure_configured()
        result = cloudinary.uploader.upload(
            io.BytesIO(file_data),
            folder=self._folder,
            resource_type="image",
            use_filename=True,
            unique_filename=True,
            overwrite=False,
        )
        return result["secure_url"]
