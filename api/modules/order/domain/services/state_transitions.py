"""Single source of truth for order state transitions and cancellability.

Both the operational lifecycle (`advance_state`, `update_order_status`) and the
agent-facing flows (`confirm`, `cancel`) MUST delegate here. The rule encodes
payment-type conditions so the machine stays coherent and reachable:

    ONLINE : DRAFT -> PENDING -> PAID -> CONFIRMED -> IN_PREPARATION -> READY -> DELIVERED/PICKED_UP
    CASH   : DRAFT -> PENDING -> CONFIRMED -> IN_PREPARATION -> READY -> DELIVERED/PICKED_UP

Cancellation is allowed only before preparation starts (RN-007/RN-018).
"""
from __future__ import annotations

from typing import Optional

from modules.order.domain.models.order_state import OrderState
from modules.order.domain.models.payment_method import PaymentMethod

# States that may be cancelled through the normal path (before preparation).
CANCELLABLE_STATES = frozenset(
    {
        OrderState.DRAFT,
        OrderState.PENDING,
        OrderState.PAID,
        OrderState.CONFIRMED,
    }
)

# Transitions that do not depend on the payment type.
_BASE_TRANSITIONS: dict[OrderState, frozenset[OrderState]] = {
    # A manual (in place) draft is accepted by the operator, so CONFIRMED is a
    # valid draft outcome alongside starting the settlement flow (PENDING).
    OrderState.DRAFT: frozenset(
        {OrderState.PENDING, OrderState.CONFIRMED, OrderState.CANCELLED}
    ),
    OrderState.PENDING: frozenset({OrderState.CANCELLED}),
    OrderState.PAID: frozenset({OrderState.CONFIRMED, OrderState.CANCELLED}),
    OrderState.CONFIRMED: frozenset({OrderState.IN_PREPARATION, OrderState.CANCELLED}),
    OrderState.IN_PREPARATION: frozenset({OrderState.READY}),
    OrderState.READY: frozenset({OrderState.DELIVERED, OrderState.PICKED_UP}),
    OrderState.DELIVERED: frozenset(),
    OrderState.PICKED_UP: frozenset(),
    OrderState.CANCELLED: frozenset(),
}


def allowed_transitions(
    status: OrderState, payment_type: Optional[PaymentMethod] = None
) -> frozenset[OrderState]:
    """Return every state reachable from ``status`` under ``payment_type``."""
    allowed = set(_BASE_TRANSITIONS.get(status, frozenset()))

    if status is OrderState.PENDING:
        # Cash acceptance reaches CONFIRMED without a prior online payment;
        # online approval reaches PAID. Neither is valid for the other type.
        if payment_type is PaymentMethod.CASH:
            allowed.add(OrderState.CONFIRMED)
        elif payment_type is PaymentMethod.ONLINE:
            allowed.add(OrderState.PAID)
        else:
            # Unspecified payment method (legacy/manual orders that never
            # captured it): the operator knows how it was settled, so both
            # forward transitions stay available. Orders that DO declare a
            # method keep the strict, type-specific transition.
            allowed.update({OrderState.PAID, OrderState.CONFIRMED})

    return frozenset(allowed)


def can_transition(
    status: OrderState,
    target: OrderState,
    payment_type: Optional[PaymentMethod] = None,
) -> bool:
    """Whether ``status -> target`` is legal for the given payment type."""
    return target in allowed_transitions(status, payment_type)


def is_cancellable(status: OrderState) -> bool:
    """Whether the order can be cancelled through the normal path."""
    return status in CANCELLABLE_STATES
