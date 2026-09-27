from abc import ABC, abstractmethod
from dataclasses import dataclass, field
from typing import List, Optional


@dataclass
class OrderSummaryLineDTO:
    line_id: str
    product_variant_id: str
    quantity: int
    unit_price: Optional[str]
    subtotal: str
    # Human-readable labels (resolved from the catalog when available); used by
    # the customer-facing confirmation message.
    product_name: Optional[str] = None
    variant_name: Optional[str] = None
    modifiers: List[dict] = field(default_factory=list)
    removed_ingredients: List[dict] = field(default_factory=list)


@dataclass
class OrderSummaryDTO:
    order_id: str
    status: str
    version: int
    lines: List[OrderSummaryLineDTO]
    subtotal: str
    discount: str
    shipping_cost: Optional[str]
    total_amount: Optional[str]
    delivery_type: Optional[str]
    address: Optional[dict]
    payment_type: Optional[str]
    estimated_time: Optional[int]
    client_id: Optional[str]
    client_name: Optional[str]
    # Real rules the order still needs satisfied before it can be confirmed.
    missing_requirements: List[str] = field(default_factory=list)


class GetOrderSummaryPort(ABC):
    @abstractmethod
    def execute(self, order_id: str) -> OrderSummaryDTO:
        pass
