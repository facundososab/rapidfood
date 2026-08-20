from dataclasses import dataclass
from typing import Optional, Protocol


@dataclass(frozen=True)
class CreateProductCommand:
    name: str
    description: str
    category_id: str
    image_url: Optional[str] = None


@dataclass(frozen=True)
class CreateProductResponse:
    id: str
    name: str
    description: str
    image_url: Optional[str]
    state: str
    category_id: str


class CreateProductPort(Protocol):
    def execute(self, command: CreateProductCommand) -> CreateProductResponse: ...