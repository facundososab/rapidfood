"""Reopen-aware, idempotent apply-coupon use case.

Coupon validation and the discount amount belong to ``config_coupon``; this use
case never computes them. The coupon snapshot and the applied-coupon history row
are written inside the same transaction as the order mutation.
"""
from __future__ import annotations

from decimal import Decimal

from modules.order.application.idempotency_key import build_idempotency_key
from modules.order.application.order_modification import prepare_order_for_modification
from modules.order.application.ports.driven.applied_coupon_repository import (
    AppliedCouponSnapshot,
)
from modules.order.application.ports.driven.clock import ClockPort
from modules.order.application.ports.driven.coupon_query import CouponQueryPort
from modules.order.application.ports.driven.idempotency import (
    IdempotentOrderMutationPort,
    OrderMutationContext,
)
from modules.order.application.ports.driver.apply_coupon_to_order_port import (
    ApplyCouponToOrderCommand,
    ApplyCouponToOrderPort,
    ApplyCouponToOrderResponse,
)
from modules.order.domain.errors.order_errors import InvalidCouponError

_OPERATION_NAME = "apply_coupon"


class ApplyCouponToOrderUseCase(ApplyCouponToOrderPort):
    def __init__(
        self,
        coupon_query: CouponQueryPort,
        executor: IdempotentOrderMutationPort,
        clock: ClockPort,
    ) -> None:
        self._coupon_query = coupon_query
        self._executor = executor
        self._clock = clock

    def execute(self, command: ApplyCouponToOrderCommand) -> ApplyCouponToOrderResponse:
        idempotency_key = build_idempotency_key(
            business_config_id=command.business_config_id,
            conversation_id=command.conversation_id,
            external_message_id=command.external_message_id,
            operation_name=_OPERATION_NAME,
            args={"order_id": command.order_id, "coupon_code": command.coupon_code},
        )

        def mutate(ctx: OrderMutationContext) -> dict:
            order = ctx.order
            ctx.superseded_attempt_ids.extend(
                prepare_order_for_modification(order, ctx.attempts, self._clock.now())
            )

            if not order.lines:
                raise InvalidCouponError("Cannot apply a coupon to an empty order")

            coupon = self._coupon_query.validate_coupon(
                command.coupon_code, order.subtotal
            )
            if coupon is None or not coupon.is_valid:
                raise InvalidCouponError(
                    f"Coupon {command.coupon_code} is invalid or expired"
                )

            order.discount = coupon.discount_amount
            order.applied_coupon_id = coupon.coupon_id
            order.coupon_code = coupon.coupon_code
            order.mark_modified()

            ctx.coupon_history.add(
                AppliedCouponSnapshot(
                    order_id=order.id,
                    coupon_id=coupon.coupon_id,
                    coupon_code=coupon.coupon_code,
                    coupon_type=coupon.coupon_type or "",
                    amount=coupon.amount or Decimal("0"),
                    discount_amount=coupon.discount_amount,
                    available_uses=coupon.available_uses or 0,
                    date_of_expiration=coupon.date_of_expiration,
                    applied_at=self._clock.now(),
                )
            )

            return {
                "order_id": order.id,
                "coupon_code": order.coupon_code,
                "discount_applied": str(order.discount),
                "total_amount": str(order.total_amount),
                "version": order.version,
            }

        outcome = self._executor.execute(
            business_config_id=command.business_config_id,
            idempotency_key=idempotency_key,
            operation_name=_OPERATION_NAME,
            order_id=command.order_id,
            mutate=mutate,
        )

        return ApplyCouponToOrderResponse(
            replayed=outcome.replayed,
            superseded_attempt_ids=outcome.superseded_attempt_ids,
            **outcome.result,
        )
