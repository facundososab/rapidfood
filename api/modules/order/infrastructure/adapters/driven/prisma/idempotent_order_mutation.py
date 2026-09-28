"""Prisma implementation of the order idempotency executor.

Everything happens inside ONE transaction:
    1. lock the order row (serializes same-order mutations),
    2. claim the idempotency key (replay the stored result when already claimed),
    3. load the aggregate, apply the mutation, persist it and the operation row,
    4. commit.

On a retry with the same key the stored result is returned and the mutation is
NOT executed again.
"""
from __future__ import annotations

from typing import Any, Callable, Optional
from uuid import uuid4

from prisma import Json

from modules.order.application.ports.driven.idempotency import (
    IdempotentMutationOutcome,
    IdempotentOrderMutationPort,
    OrderMutationContext,
)
from modules.order.application.ports.driven.applied_coupon_repository import (
    AppliedCouponRepositoryPort,
)
from modules.order.application.ports.driven.payment_attempt_query import (
    PaymentAttemptQueryPort,
)
from modules.order.domain.errors.order_errors import OrderNotFound
from modules.order.domain.models.order import Order
from modules.order.infrastructure.adapters.driven.prisma.applied_coupon_repository import (
    PrismaAppliedCouponRepository,
)
from modules.order.infrastructure.adapters.driven.prisma.order_repository import (
    load_order_in_tx,
    persist_order_in_tx,
)
from modules.order.infrastructure.adapters.driven.prisma.payment_attempt_query import (
    PrismaPaymentAttemptQuery,
)

# Row lock: two concurrent mutations of the same order must not lose updates.
# The explicit cast is required: the driver sends the id as text and the column is uuid.
_LOCK_ORDER_SQL = 'SELECT "order_id" FROM "order" WHERE "order_id" = $1::uuid FOR UPDATE'
_OPERATION_STATUS_COMPLETED = "COMPLETED"


class PrismaIdempotentOrderMutation(IdempotentOrderMutationPort):
    def __init__(
        self,
        client: Any,
        attempts_factory: Optional[Callable[[Any], PaymentAttemptQueryPort]] = None,
        coupon_history_factory: Optional[
            Callable[[Any], AppliedCouponRepositoryPort]
        ] = None,
    ) -> None:
        self._client = client
        self._attempts_factory = attempts_factory or PrismaPaymentAttemptQuery
        self._coupon_history_factory = (
            coupon_history_factory or PrismaAppliedCouponRepository
        )

    def execute(
        self,
        *,
        business_config_id: str,
        idempotency_key: str,
        operation_name: str,
        order_id: str,
        mutate: Callable[[OrderMutationContext], dict],
    ) -> IdempotentMutationOutcome:
        with self._client.tx() as tx:
            tx.query_raw(_LOCK_ORDER_SQL, order_id)

            existing = tx.idempotentoperation.find_unique(
                where={
                    "businessConfigId_idempotencyKey": {
                        "businessConfigId": business_config_id,
                        "idempotencyKey": idempotency_key,
                    }
                }
            )
            if existing is not None:
                return IdempotentMutationOutcome(
                    replayed=True,
                    result=dict(existing.result or {}),
                )

            order = load_order_in_tx(tx, order_id)
            if order is None:
                raise OrderNotFound(f"Order {order_id} not found")

            ctx = OrderMutationContext(
                order=order,
                attempts=self._attempts_factory(tx),
                coupon_history=self._coupon_history_factory(tx),
            )
            result = mutate(ctx)

            persist_order_in_tx(tx, order)
            tx.idempotentoperation.create(
                {
                    "id": str(uuid4()),
                    "businessConfigId": business_config_id,
                    "idempotencyKey": idempotency_key,
                    "operationName": operation_name,
                    "status": _OPERATION_STATUS_COMPLETED,
                    "result": Json(result),
                }
            )

            return IdempotentMutationOutcome(
                replayed=False,
                result=result,
                superseded_attempt_ids=tuple(ctx.superseded_attempt_ids),
            )
