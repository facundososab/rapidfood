from dataclasses import dataclass
from decimal import Decimal


@dataclass
class ModifierOption:
    id: str
    modifier_group_id: str
    name: str
    price_delta: Decimal
    available: bool = True

    def __post_init__(self) -> None:
        if self.price_delta < Decimal("0"):
            raise ValueError("price_delta cannot be negative")
