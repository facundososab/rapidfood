from decimal import Decimal
from typing import Protocol


class ProductQueryPort(Protocol):
    """Puerto publico que consumen otros bounded contexts."""

    def get_current_price(self, product_id: str) -> Decimal: ...

    def is_available(self, product_id: str) -> bool: ...