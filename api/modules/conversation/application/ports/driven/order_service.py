"""Driven port: order capabilities the agent needs.

Conversation-owned DTOs only. The concrete adapter delegates to the order
module's public driver ports (including the reopen-aware, idempotent mutations).
``business_config_id`` / ``conversation_id`` / ``external_message_id`` always
come from the trusted context, never from the model.
"""
from __future__ import annotations

from dataclasses import dataclass, field
from typing import Optional, Protocol, Tuple


@dataclass(frozen=True, slots=True)
class CurrentOrderDTO:
    found: bool
    order_id: Optional[str] = None
    status: Optional[str] = None
    version: Optional[int] = None
    editable: bool = False
    requires_reopen: bool = False
    requires_new_order: bool = False


@dataclass(frozen=True, slots=True)
class OrderLineModifierDTO:
    id: str
    name: str
    price_delta: Optional[str] = None


@dataclass(frozen=True, slots=True)
class OrderLineRemovedIngredientDTO:
    id: str
    name: str


@dataclass(frozen=True, slots=True)
class OrderLineDTO:
    line_id: str
    product_variant_id: str
    quantity: int
    unit_price: Optional[str]
    subtotal: str
    modifiers: Tuple[OrderLineModifierDTO, ...] = field(default_factory=tuple)
    removed_ingredients: Tuple[OrderLineRemovedIngredientDTO, ...] = field(
        default_factory=tuple
    )


@dataclass(frozen=True, slots=True)
class OrderSummaryDTO:
    order_id: str
    status: str
    version: int
    lines: Tuple[OrderLineDTO, ...]
    subtotal: str
    discount: str
    shipping_cost: Optional[str]
    total_amount: Optional[str]
    delivery_type: Optional[str]
    address: Optional[dict]
    payment_type: Optional[str]
    estimated_time: Optional[int]
    missing_requirements: Tuple[str, ...] = field(default_factory=tuple)


@dataclass(frozen=True, slots=True)
class OrderMutationDTO:
    order_id: str
    version: int
    replayed: bool = False
    line_id: Optional[str] = None
    line_count: Optional[int] = None
    total_amount: Optional[str] = None
    shipping_cost: Optional[str] = None


@dataclass(frozen=True, slots=True)
class OrderStatusDTO:
    order_id: str
    status: str
    estimated_time: Optional[int] = None
    total_amount: Optional[str] = None


@dataclass(frozen=True, slots=True)
class CheckoutDTO:
    order_id: str
    checkout_url: str
    payment_attempt_id: str
    status: str
    order_version: int


class OrderServicePort(Protocol):
    # Reads
    def get_current_order(
        self, business_config_id: str, conversation_id: str
    ) -> CurrentOrderDTO: ...

    def get_latest_active_order(
        self,
        business_config_id: str,
        client_id: Optional[str] = None,
        conversation_id: Optional[str] = None,
    ) -> Optional[OrderStatusDTO]: ...

    def get_order_summary(self, order_id: str) -> OrderSummaryDTO: ...

    # Draft resolution (creation reuses the order module's start-draft flow)
    def get_or_create_current_draft(
        self,
        *,
        business_config_id: str,
        conversation_id: str,
        client_id: Optional[str] = None,
        client_name: Optional[str] = None,
    ) -> str: ...

    # Mutations (reopen-aware + idempotent on the order side)
    def add_item(
        self,
        *,
        business_config_id: str,
        conversation_id: Optional[str],
        external_message_id: str,
        order_id: str,
        product_variant_id: str,
        quantity: int,
        modifier_option_ids: list[str],
        removed_ingredient_ids: list[str],
    ) -> OrderMutationDTO: ...

    def update_item(
        self,
        *,
        business_config_id: str,
        conversation_id: Optional[str],
        external_message_id: str,
        order_id: str,
        line_id: str,
        quantity: Optional[int] = None,
        modifier_option_ids: Optional[list[str]] = None,
        removed_ingredient_ids: Optional[list[str]] = None,
    ) -> OrderMutationDTO: ...

    def remove_item(
        self,
        *,
        business_config_id: str,
        conversation_id: Optional[str],
        external_message_id: str,
        order_id: str,
        line_id: str,
    ) -> OrderMutationDTO: ...

    def set_delivery(
        self,
        *,
        business_config_id: str,
        conversation_id: Optional[str],
        external_message_id: str,
        order_id: str,
        address: dict,
    ) -> OrderMutationDTO: ...

    def set_pickup(
        self,
        *,
        business_config_id: str,
        conversation_id: Optional[str],
        external_message_id: str,
        order_id: str,
    ) -> OrderMutationDTO: ...

    def set_payment_type(self, order_id: str, payment_type: str) -> None: ...

    def set_client(
        self,
        order_id: str,
        client_name: Optional[str] = None,
        client_id: Optional[str] = None,
    ) -> None: ...

    def apply_coupon(
        self,
        *,
        business_config_id: str,
        conversation_id: Optional[str],
        external_message_id: str,
        order_id: str,
        coupon_code: str,
    ) -> OrderMutationDTO: ...

    def confirm_order(self, order_id: str) -> OrderStatusDTO: ...

    def cancel_order(self, order_id: str) -> OrderStatusDTO: ...

    def create_payment_checkout(self, order_id: str) -> CheckoutDTO: ...
