from decimal import Decimal
from dataclasses import dataclass, field
from datetime import datetime
from typing import List, Optional

from modules.order.domain.models.order_state import OrderState
from modules.order.domain.models.delivery_type import DeliveryType
from modules.order.domain.models.payment_method import PaymentMethod
from modules.order.domain.models.order_line import OrderLine
from modules.order.domain.errors.order_errors import OrderStateError, InvalidLineError


@dataclass
class Order:
    """
    Represents an Order Aggregate Root (ADR-4).
    Enforces business rules regarding state transitions and calculations.
    """
    id: str
    status: OrderState
    subtotal: Decimal
    discount: Decimal
    client_id: Optional[str] = None
    address_id: Optional[str] = None
    conversation_id: Optional[str] = None
    estimated_time: Optional[int] = None
    delivery_type: Optional[DeliveryType] = None
    payment_type: Optional[PaymentMethod] = None
    shipping_cost: Optional[Decimal] = None
    total_amount: Optional[Decimal] = None
    applied_coupon_id: Optional[str] = None
    confirmed_at: Optional[datetime] = None
    created_at: Optional[datetime] = None
    lines: List[OrderLine] = field(default_factory=list)

    def is_draft(self) -> bool:
        return self.status == OrderState.DRAFT

    def can_be_modified(self) -> bool:
        """Only DRAFT orders can have lines added/removed (RN-020)."""
        return self.is_draft()

    def add_line(self, line: OrderLine):
        if not self.can_be_modified():
            raise OrderStateError("Cannot add lines to a non-draft order")
        if line.quantity <= 0:
            raise InvalidLineError("Quantity must be greater than 0")
        
        # Upsert line
        existing_line = next((l for l in self.lines if l.product_id == line.product_id), None)
        if existing_line:
            existing_line.quantity = line.quantity
            existing_line.subtotal = line.subtotal
        else:
            self.lines.append(line)
            
        self._recalculate_totals()

    def remove_line(self, product_id: str):
        if not self.can_be_modified():
            raise OrderStateError("Cannot remove lines from a non-draft order")
        self.lines = [l for l in self.lines if l.product_id != product_id]
        self._recalculate_totals()

    def _recalculate_totals(self):
        """
        Subtotal is the sum of line subtotals.
        Total is Subtotal - Discount + Shipping Cost.
        """
        self.subtotal = sum((line.subtotal for line in self.lines), Decimal("0.0"))
        
        total = self.subtotal - self.discount
        if self.shipping_cost:
            total += self.shipping_cost
            
        self.total_amount = max(total, Decimal("0.0"))

    def set_delivery_details(self, delivery_type: DeliveryType, address_id: Optional[str] = None, shipping_cost: Optional[Decimal] = None):
        if not self.is_draft() and self.status != OrderState.PENDING:
            raise OrderStateError("Cannot change delivery details after confirmation.")
        
        self.delivery_type = delivery_type
        if delivery_type == DeliveryType.DELIVERY:
            self.address_id = address_id
            self.shipping_cost = shipping_cost or Decimal("0.0")
        else:
            self.address_id = None
            self.shipping_cost = Decimal("0.0")
            
        self._recalculate_totals()

    def confirm(self):
        """Transition from DRAFT -> PENDING (RN-020)."""
        if not self.is_draft():
            raise OrderStateError(f"Cannot confirm order in state {self.status}")
        if not self.lines:
            raise OrderStateError("Cannot confirm order without lines")
        
        self.status = OrderState.PENDING
        # Freeze prices would happen here if we passed a catalog snapshot,
        # but typically the use case handles fetching current prices and saving them.
