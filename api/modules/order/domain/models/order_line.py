from dataclasses import dataclass, field
from decimal import Decimal
from typing import Optional, List

from modules.order.domain.models.order_line_modifier import OrderLineModifier
from modules.order.domain.models.order_line_removed_ingredient import OrderLineRemovedIngredient


@dataclass
class OrderLine:
    """
    Represents a single variant line in an Order.
    Entity within the Order aggregate.
    """
    id: str
    order_id: str
    product_variant_id: str
    quantity: int
    unit_price: Optional[Decimal]  # None in DRAFT; frozen at confirmation
    subtotal: Decimal
    discount_id: Optional[str] = None
    modifiers: List[OrderLineModifier] = field(default_factory=list)
    removed_ingredients: List[OrderLineRemovedIngredient] = field(default_factory=list)
