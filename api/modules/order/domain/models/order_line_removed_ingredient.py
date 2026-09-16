from dataclasses import dataclass
from typing import Optional


@dataclass
class OrderLineRemovedIngredient:
    """
    Records an ingredient removed from an OrderLine.
    Name snapshot frozen at confirmation.
    """
    id: str
    order_line_id: str
    ingredient_id: str
    ingredient_name_snapshot: str
