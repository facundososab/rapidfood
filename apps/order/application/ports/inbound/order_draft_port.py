"""Order draft port — INBOUND (owned by ``apps.order``, exposed to the conversation agent).

Contract only: the conversation agent drives draft ordering through this port
(create/add/remove lines, coupons, confirm, abandon). Implemented by the
order app's use cases in a later change. ``status`` is an ``OrderStatus`` value.
"""

from dataclasses import dataclass
from decimal import Decimal
from typing import Protocol


@dataclass(frozen=True)
class OrderLineDTO:
    order_line_id: str
    product_id: str
    amount: int
    unit_price: Decimal | None
    subtotal: Decimal


@dataclass(frozen=True)
class OrderDTO:
    order_id: str
    client_id: str | None
    conversation_id: str | None
    status: str  # OrderStatus value
    delivery_type: str | None
    payment_type: str | None
    shipping_cost: Decimal | None
    total_amount: Decimal | None
    lines: tuple[OrderLineDTO, ...]


class OrderDraftPort(Protocol):
    def create_draft(self, client_id: str, conversation_id: str) -> OrderDTO: ...
    def get_draft_by_conversation(self, conversation_id: str) -> OrderDTO | None: ...  # REQ-038 / RN-028
    def add_line(self, order_id: str, product_id: str, amount: int) -> OrderDTO: ...  # upsert per @@unique
    def remove_line(self, order_id: str, order_line_id: str) -> OrderDTO: ...
    def set_quantity(self, order_id: str, order_line_id: str, amount: int) -> OrderDTO: ...
    def apply_coupon(self, order_id: str, coupon_id: str) -> OrderDTO: ...
    def remove_coupon(self, order_id: str, applied_coupon_id: str) -> OrderDTO: ...  # REQ-020 "quitar cupones"
    def confirm(self, order_id: str) -> OrderDTO: ...  # BORRADOR→PENDIENTE, all RN-004/023 validations
    def abandon(self, order_id: str) -> None: ...  # RN-009
