from typing import Protocol


class ImageStoragePort(Protocol):
    """Driven port: uploads a raw image file and returns its public URL."""

    def upload(self, file_data: bytes, filename: str, content_type: str) -> str:
        """Upload *file_data* and return the permanent public URL."""
        ...
