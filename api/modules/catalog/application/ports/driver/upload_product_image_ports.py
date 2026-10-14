from dataclasses import dataclass
from typing import Protocol


@dataclass(frozen=True)
class UploadProductImageCommand:
    product_id: str
    file_data: bytes
    filename: str


@dataclass(frozen=True)
class UploadProductImageResponse:
    image_url: str


class UploadProductImagePort(Protocol):
    def execute(
        self, command: UploadProductImageCommand
    ) -> UploadProductImageResponse: ...
