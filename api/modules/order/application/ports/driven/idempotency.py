"""Order idempotency driven port.

Channel-neutral: the same contract serves LangChain tools, WhatsApp, HTTP or any
future channel. The executor claims the idempotency key, applies the mutation
and persists the operation result inside ONE database transaction, so an
intermediate failure can never leave the claim and the mutation out of sync.

The mutation callback receives an ``OrderMutationContext`` whose payment-attempt
port is bound to the same transaction, letting a caller reopen a pending online
order and supersede its old checkout atomically with the modification.
"""
from __future__ import annotations

from dataclasses import dataclass, field
from typing import Callable, Optional, Protocol

from modules.order.application.ports.driven.applied_coupon_repository import (
    AppliedCouponRepositoryPort,
)
from modules.order.application.ports.driven.payment_attempt_query import (
    PaymentAttemptQueryPort,
)
from modules.order.domain.models.order import Order


@dataclass(slots=True)
class OrderMutationContext:
    """Everything a mutation callback may touch inside the transaction."""

    order: Order
    attempts: PaymentAttemptQueryPort
    coupon_history: AppliedCouponRepositoryPort
    # Filled by the callback when a reopen superseded a checkout. The executor
    # surfaces the ids so the caller can cancel them remotely AFTER the commit.
    superseded_attempt_ids: list[str] = field(default_factory=list)


@dataclass(frozen=True, slots=True)
class IdempotentMutationOutcome:
    """Result of an idempotent mutation.

    ``replayed`` is True when the exact same logical operation had already been
    executed, in which case ``result`` is the stored result and the mutation
    did NOT run again.
    """

    replayed: bool
    result: dict
    superseded_attempt_ids: tuple[str, ...] = ()


class IdempotentOrderMutationPort(Protocol):
    def execute(
        self,
        *,
        business_config_id: str,
        idempotency_key: str,
        operation_name: str,
        order_id: str,
        mutate: Callable[[OrderMutationContext], dict],
    ) -> IdempotentMutationOutcome: ...


@dataclass(frozen=True, slots=True)
class IdempotentOperationRecord:
    id: str
    business_config_id: str
    idempotency_key: str
    operation_name: str
    status: str
    result: Optional[dict] = None
