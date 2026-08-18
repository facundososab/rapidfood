from decimal import Decimal
from dataclasses import dataclass
from typing import Optional


@dataclass
class OrderLine:
    """
    Represents a single product line in an Order.
    This is an Entity, part of the Order aggregate.
    """
    id: str
    order_id: str
    product_id: str
    quantity: int
    unit_price: Optional[Decimal]  # Null in DRAFT state
    subtotal: Decimal
    discount_id: Optional[str] = None
