from dataclasses import dataclass
from typing import Protocol


@dataclass(frozen=True)
class UploadProductImageCommand:
    product_id: str
    file_data: bytes
    filename: str
    content_type: str


class UploadProductImagePort(Protocol):
    def execute(self, command: UploadProductImageCommand) -> str:
        """Returns the public URL of the uploaded image."""
        ...
