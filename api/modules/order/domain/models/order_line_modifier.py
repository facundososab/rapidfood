from dataclasses import dataclass
from decimal import Decimal
from typing import Optional


@dataclass
class OrderLineModifier:
    """
    Records a modifier option selected for an OrderLine.
    Snapshots are NULL during DRAFT; frozen at confirmation.
    """
    id: str
    order_line_id: str
    modifier_option_id: str
    option_name_snapshot: str
    price_delta: Optional[Decimal] = None  # frozen at confirmation
