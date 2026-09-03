from dataclasses import dataclass
from decimal import Decimal
from typing import Optional, Protocol


@dataclass(frozen=True)
class ProductSnapshot:
    """Current price and availability of a product (public contract DTO)."""

    product_id: str
    price: Decimal
    is_available: bool


class ProductQueryPort(Protocol):
    """Puerto publico que consumen otros bounded contexts."""

    def get_current_price(self, product_id: str) -> Decimal: ...

    def is_available(self, product_id: str) -> bool: ...

    def find_product(self, product_id: str) -> Optional[ProductSnapshot]:
        """Total query: ``None`` when the product or its current price is missing."""