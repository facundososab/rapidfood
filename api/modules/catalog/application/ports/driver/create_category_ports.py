from dataclasses import dataclass
from typing import Protocol


@dataclass(frozen=True)
class CreateCategoryCommand:
    description: str


@dataclass(frozen=True)
class CreateCategoryResponse:
    id: str
    description: str


class CreateCategoryPort(Protocol):
    def execute(self, command: CreateCategoryCommand) -> CreateCategoryResponse: ...