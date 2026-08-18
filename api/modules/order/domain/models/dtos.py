from dataclasses import dataclass
from decimal import Decimal
from typing import Optional


@dataclass
class LineInputDTO:
    product_id: str
    quantity: int


@dataclass
class CreateOrderDTO:
    client_id: Optional[str] = None
    conversation_id: Optional[str] = None
