from dataclasses import dataclass
from typing import Protocol


@dataclass(frozen=True)
class CreateProductCommand:
    name: str
    description: str
    category_id: str


@dataclass(frozen=True)
class CreateProductResponse:
    id: str
    name: str
    description: str
    state: str
    category_id: str


class CreateProductPort(Protocol):
    def execute(self, command: CreateProductCommand) -> CreateProductResponse: ...