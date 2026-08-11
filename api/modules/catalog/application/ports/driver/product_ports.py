from dataclasses import dataclass
from decimal import Decimal
from typing import Protocol

from modules.catalog.domain.models.product import ProductState


@dataclass(frozen=True)
class CreateProductCommand:
    description: str
    category_id: str

@dataclass(frozen=True)
class CreateProductResponse:
    id: str
    description: str
    state: str
    category_id: str

class CreateProductPort(Protocol):
    def execute(self, command: CreateProductCommand) -> CreateProductResponse: ...


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

class ProductQueryPort(Protocol):
    """Puerto publico que consumen otros bounded contexts."""

    def get_current_price(self, product_id: str) -> Decimal: ...

    def is_available(self, product_id: str) -> bool: ...

@dataclass(frozen=True)
class ListProductsQuery:
    category_id: str | None = None
    state: ProductState | None = None


@dataclass(frozen=True)
class ProductSummary:
    id: str
    description: str
    state: str
    category_id: str


class ListProductsPort(Protocol):
    def execute(self, query: ListProductsQuery) -> list[ProductSummary]: ...