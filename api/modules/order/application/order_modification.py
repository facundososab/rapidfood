"""Modification readiness and reopen for an order.

Keeps the invariant ``modifiable <=> status == DRAFT`` while allowing an online
order awaiting payment to be reopened explicitly (see
``Order.reopen_for_modification``). A modification invalidates both the previous
checkout (superseded) and the previous confirmation (``confirmed_at`` cleared).

CQRS: ``modification_readiness`` is a pure read (used by ``get_current_order``);
``prepare_order_for_modification`` is the only place that transitions the order,
and it is always called inside the mutation transaction.
"""
from __future__ import annotations

from dataclasses import dataclass
from datetime import datetime

from modules.order.application.ports.driven.payment_attempt_query import (
    PaymentAttemptQueryPort,
)
from modules.order.domain.errors.order_errors import NewOrderRequiredError
from modules.order.domain.models.order import Order
from modules.order.domain.models.order_state import OrderState
from modules.order.domain.models.payment_method import PaymentMethod


@dataclass(frozen=True, slots=True)
class ModificationReadiness:
    editable: bool
    requires_reopen: bool
    requires_new_order: bool


def _is_reopenable(order: Order, attempts: PaymentAttemptQueryPort) -> bool:
    """A pending order can be reopened while it is still unpaid.

    The normal case is an ONLINE order awaiting payment. A PENDING order with an
    unspecified payment method (legacy/manual, or an agent order confirmed before
    the method was captured) is also unpaid, so it is reopened instead of forcing
    a brand-new order. A CASH order is accepted by the business and stays closed
    (RN-006b).
    """
    return (
        order.status is OrderState.PENDING
        and order.payment_type in (None, PaymentMethod.ONLINE)
        and not attempts.has_current_approved(order.id, order.version)
    )


def modification_readiness(
    order: Order, attempts: PaymentAttemptQueryPort
) -> ModificationReadiness:
    """Read-only editability of the current order. Never mutates."""
    if order.status is OrderState.DRAFT:
        return ModificationReadiness(
            editable=True, requires_reopen=False, requires_new_order=False
        )
    if _is_reopenable(order, attempts):
        return ModificationReadiness(
            editable=True, requires_reopen=True, requires_new_order=False
        )
    return ModificationReadiness(
        editable=False, requires_reopen=False, requires_new_order=True
    )


def prepare_order_for_modification(
    order: Order, attempts: PaymentAttemptQueryPort, at: datetime
) -> list[str]:
    """Make the order modifiable or raise.

    Returns the ids of the checkout attempts that were superseded (empty when the
    order was already a draft). The caller is expected to attempt their remote
    cancellation AFTER the transaction commits; the returned ids are what makes
    that a separate, retryable step.

    Must be called inside the mutation transaction so the reopen, the supersede
    of the previous attempt and the mutation commit together.
    """
    if order.status is OrderState.DRAFT:
        return []

    if _is_reopenable(order, attempts):
        order.reopen_for_modification(has_current_approved_payment=False)
        return attempts.supersede_current(order.id, order.version, at)

    raise NewOrderRequiredError(
        f"Order {order.id} in state {order.status.value} cannot be modified; "
        "a new order is required"
    )
