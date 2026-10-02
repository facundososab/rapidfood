from decimal import Decimal
from dataclasses import dataclass, field
from datetime import datetime
from typing import List, Optional

from modules.order.domain.models.order_state import OrderState
from modules.order.domain.models.delivery_type import DeliveryType
from modules.order.domain.models.payment_method import PaymentMethod
from modules.order.domain.models.order_origin import OrderOrigin
from modules.order.domain.models.order_line import OrderLine
from modules.order.domain.models.delivery_address import DeliveryAddress
from modules.order.domain.errors.order_errors import OrderStateError, InvalidLineError


@dataclass
class Order:
    """
    Order Aggregate Root.
    Enforces state transitions and line invariants.
    """
    id: str
    status: OrderState
    subtotal: Decimal
    discount: Decimal
    client_id: Optional[str] = None
    client_name: Optional[str] = None
    business_config_id: Optional[str] = None
    address_id: Optional[str] = None
    delivery_address: Optional[DeliveryAddress] = None
    coupon_code: Optional[str] = None
    conversation_id: Optional[str] = None
    estimated_time: Optional[int] = None
    # Delivery travel time snapshot (route duration from the delivery quote), so
    # the ETA can be recomputed at confirmation without repeating routing.
    route_duration_minutes: Optional[int] = None
    delivery_type: Optional[DeliveryType] = None
    payment_type: Optional[PaymentMethod] = None
    origin: OrderOrigin = OrderOrigin.IN_PLACE
    shipping_cost: Optional[Decimal] = None
    total_amount: Optional[Decimal] = None
    applied_coupon_id: Optional[str] = None
    confirmed_at: Optional[datetime] = None
    created_at: Optional[datetime] = None
    # Monotonic commercial snapshot version. Bumped by every mutation that
    # changes what the customer confirmed. A payment attempt is bound to the
    # version it was created for.
    version: int = 0
    lines: List[OrderLine] = field(default_factory=list)

    def is_draft(self) -> bool:
        return self.status == OrderState.DRAFT

    def can_be_modified(self) -> bool:
        """Only DRAFT orders can have lines added/removed."""
        return self.is_draft()

    def add_line(self, line: OrderLine) -> None:
        if not self.can_be_modified():
            raise OrderStateError("Cannot add lines to a non-draft order")
        if line.quantity <= 0:
            raise InvalidLineError("Quantity must be greater than 0")

        # Upsert by line ID (not by variant) — same variant can appear
        # multiple times with different modifier/ingredient configurations.
        existing = next((l for l in self.lines if l.id == line.id), None)
        if existing:
            existing.quantity = line.quantity
            existing.subtotal = line.subtotal
            existing.unit_price = line.unit_price
        else:
            self.lines.append(line)

        self._recalculate_totals()
        self._bump_version()

    def remove_line(self, line_id: str) -> None:
        if not self.can_be_modified():
            raise OrderStateError("Cannot remove lines from a non-draft order")
        self.lines = [l for l in self.lines if l.id != line_id]
        self._recalculate_totals()
        self._bump_version()

    def mark_modified(self) -> None:
        """Record that the commercial snapshot changed.

        Recomputes totals and bumps the version. Use cases that mutate the order
        without going through an aggregate method MUST call this so the version
        stays a reliable barrier for payment attempts.
        """
        self._recalculate_totals()
        self._bump_version()

    def _bump_version(self) -> None:
        self.version += 1

    def reopen_for_modification(self, has_current_approved_payment: bool = False) -> None:
        """Explicitly reopen an unpaid pending order so it can be modified.

        Keeps the invariant ``modifiable <=> status == DRAFT``. Valid for an order
        awaiting payment: ONLINE, or with an unspecified method (legacy/manual or
        an agent order confirmed before the method was captured). Once a payment
        for the current version is approved the snapshot is final and a new order
        is required.

        Clears ``confirmed_at`` because the previous confirmation no longer
        describes the new snapshot.
        """
        if self.status is not OrderState.PENDING:
            raise OrderStateError(
                f"Cannot reopen an order in state {self.status.value}"
            )
        if self.payment_type not in (None, PaymentMethod.ONLINE):
            raise OrderStateError(
                "Only unpaid orders awaiting payment can be reopened for modification"
            )
        if has_current_approved_payment:
            raise OrderStateError(
                "A payment for the current version was approved; the order is final"
            )
        self.status = OrderState.DRAFT
        self.confirmed_at = None

    def _recalculate_totals(self) -> None:
        self.subtotal = sum((line.subtotal for line in self.lines), Decimal("0"))
        total = self.subtotal - self.discount
        if self.shipping_cost:
            total += self.shipping_cost
        self.total_amount = max(total, Decimal("0"))

    def set_delivery_details(
        self,
        delivery_type: DeliveryType,
        address_id: Optional[str] = None,
        shipping_cost: Optional[Decimal] = None,
    ) -> None:
        if not self.is_draft() and self.status != OrderState.PENDING:
            raise OrderStateError("Cannot change delivery details after confirmation.")
        self.delivery_type = delivery_type
        if delivery_type == DeliveryType.DELIVERY:
            self.address_id = address_id
            self.shipping_cost = shipping_cost or Decimal("0")
        else:
            self.address_id = None
            self.shipping_cost = Decimal("0")
        self._recalculate_totals()
        self._bump_version()

    def confirm(self) -> None:
        """Confirm the draft and record the confirmation time.

        A manual order (POS / in place) is taken and settled by the operator, so
        it counts as accepted immediately: ``DRAFT -> CONFIRMED``. An agent order
        still awaits settlement first: ``DRAFT -> PENDING`` (an approved online
        payment moves it to PAID; cash acceptance moves it to CONFIRMED).

        ``PAID`` is intentionally NOT used for manual orders: it means a
        provider-verified online payment approval, which only the payment webhook
        can assert.
        """
        if not self.is_draft():
            raise OrderStateError(f"Cannot confirm order in state {self.status}")
        if not self.lines:
            raise OrderStateError("Cannot confirm an empty order")
        self.status = (
            OrderState.CONFIRMED
            if self.origin is OrderOrigin.IN_PLACE
            else OrderState.PENDING
        )
        self.confirmed_at = datetime.utcnow()
