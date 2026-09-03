from dataclasses import dataclass
from typing import Optional, Protocol

from modules.catalog.domain.models.product import ProductState


@dataclass(frozen=True)
class ListProductsQuery:
    category_id: str | None = None
    state: ProductState | None = None


@dataclass(frozen=True)
class ProductSummary:
    id: str
    name: str
    description: str
    image_url: Optional[str]
    state: str
    category_id: str


class ListProductsPort(Protocol):
    def execute(self, query: ListProductsQuery) -> list[ProductSummary]: ...