from dataclasses import dataclass
from typing import Protocol


@dataclass(frozen=True)
class DeleteProductCommand:
    product_id: str


@dataclass(frozen=True)
class DeleteProductResponse:
    id: str


class DeleteProductPort(Protocol):
    def execute(self, command: DeleteProductCommand) -> DeleteProductResponse: ...