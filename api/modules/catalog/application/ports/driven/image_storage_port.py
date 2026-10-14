from dataclasses import dataclass
from typing import Protocol


class ImageStorageError(Exception):
    """Raised when the image storage backend cannot complete an operation."""


@dataclass(frozen=True)
class StoredImage:
    """A successfully stored image: its public URL and backend identifier."""

    url: str
    public_id: str


class ImageStoragePort(Protocol):
    """Driven port: stores a raw image file in an external object store."""

    def upload(
        self, file_data: bytes, filename: str, public_id: str
    ) -> StoredImage:
        """Store *file_data* under *public_id* and return the stored image."""
        ...

    def delete(self, public_id: str) -> None:
        """Delete a previously stored image. Best-effort cleanup."""
        ...
