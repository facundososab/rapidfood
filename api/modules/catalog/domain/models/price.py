from dataclasses import dataclass
from datetime import date
from decimal import Decimal

@dataclass(frozen=True)
class Price:
    id: str
    product_id: str
    since_date: date
    price: Decimal

    def __post_init__(self) -> None:
        if self.price < Decimal("0"):
            raise ValueError("El precio no puede ser negativo")