from dataclasses import dataclass
from typing import List, Optional, Protocol

from modules.catalog.domain.models.category import Category
from modules.catalog.domain.models.price import Price


@dataclass(frozen=True)
class ProductDetail:
    id: str
    name: str
    description: str
    state: str
    category_id: str
    category: Optional[Category]
    prices: List[Price]


class GetProductPort(Protocol):
    def execute(self, product_id: str) -> ProductDetail: ...