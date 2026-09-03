from dataclasses import dataclass
from typing import Protocol

from modules.catalog.domain.models.product import ProductState


@dataclass(frozen=True)
class SetProductStateCommand:
    product_id: str
    state: ProductState


@dataclass(frozen=True)
class SetProductStateResponse:
    id: str
    state: str


class SetProductStatePort(Protocol):
    def execute(self, command: SetProductStateCommand) -> SetProductStateResponse: ...