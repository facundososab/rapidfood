from dataclasses import dataclass
from decimal import Decimal
from typing import Optional


@dataclass
class Discount:
    id: str
    percentage: Decimal
    product_id: Optional[str] = None

    def __post_init__(self) -> None:
        if not (Decimal("0") <= self.percentage <= Decimal("100")):
            raise ValueError("El porcentaje debe estar entre 0 y 100")

    def is_global(self) -> bool:
        return self.product_id is None

    def applies_to(self, product_id: str) -> bool:
        return self.is_global() or self.product_id == product_id

    def calculate_discount_amount(self, subtotal: Decimal) -> Decimal:
        return subtotal * self.percentage / Decimal("100")

    