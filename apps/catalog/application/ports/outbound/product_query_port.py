"""Product query port — outbound (owned by ``apps.catalog``).

Contract only. The current price is ``max(since_date) <= now`` (use-case rule,
implemented by the catalog adapter).
"""

from dataclasses import dataclass
from datetime import datetime
from decimal import Decimal
from typing import Protocol


@dataclass(frozen=True)
class ProductDTO:
    product_id: str
    description: str
    available: bool
    category_id: str


@dataclass(frozen=True)
class PriceDTO:
    price_id: str
    product_id: str
    since_date: datetime
    price: Decimal


class ProductQueryPort(Protocol):
    def find_available_by_id(self, product_id: str) -> ProductDTO | None: ...
    def list_available(self) -> list[ProductDTO]: ...
    def find_current_price(self, product_id: str) -> PriceDTO | None: ...
