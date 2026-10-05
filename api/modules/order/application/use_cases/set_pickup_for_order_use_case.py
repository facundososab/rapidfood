"""Reopen-aware, idempotent set-pickup use case.

Selecting pickup clears any delivery snapshot and shipping cost. The order
module owns that cleanup, not the caller.
"""
from __future__ import annotations

from decimal import Decimal
from typing import Optional

from modules.order.application.idempotency_key import build_idempotency_key
from modules.order.application.order_modification import prepare_order_for_modification
from modules.order.application.ports.driven.clock import ClockPort
from modules.order.application.ports.driven.idempotency import (
    IdempotentOrderMutationPort,
    OrderMutationContext,
)
from modules.order.application.ports.driver.set_pickup_for_order_port import (
    SetPickupForOrderCommand,
    SetPickupForOrderPort,
    SetPickupForOrderResponse,
)
from modules.order.domain.models.delivery_type import DeliveryType

_OPERATION_NAME = "set_pickup"


class SetPickupForOrderUseCase(SetPickupForOrderPort):
    def __init__(
        self,
        executor: IdempotentOrderMutationPort,
        clock: ClockPort,
        prep_time_estimator: Optional[object] = None,
    ) -> None:
        self._executor = executor
        self._clock = clock
        self._prep_time_estimator = prep_time_estimator

    def execute(self, command: SetPickupForOrderCommand) -> SetPickupForOrderResponse:
        idempotency_key = build_idempotency_key(
            business_config_id=command.business_config_id,
            conversation_id=command.conversation_id,
            external_message_id=command.external_message_id,
            operation_name=_OPERATION_NAME,
            args={"order_id": command.order_id},
        )

        estimated_time = self._estimate_time(command.business_config_id)

        def mutate(ctx: OrderMutationContext) -> dict:
            order = ctx.order
            ctx.superseded_attempt_ids.extend(
                prepare_order_for_modification(order, ctx.attempts, self._clock.now())
            )

            order.delivery_type = DeliveryType.PICKUP
            order.delivery_address = None
            order.address_id = None
            order.shipping_cost = Decimal("0")
            order.route_duration_minutes = None
            order.estimated_time = estimated_time
            order.mark_modified()

            return {"order_id": order.id, "version": order.version}

        outcome = self._executor.execute(
            business_config_id=command.business_config_id,
            idempotency_key=idempotency_key,
            operation_name=_OPERATION_NAME,
            order_id=command.order_id,
            mutate=mutate,
        )

        return SetPickupForOrderResponse(
            replayed=outcome.replayed,
            superseded_attempt_ids=outcome.superseded_attempt_ids,
            **outcome.result,
        )

    def _estimate_time(self, business_config_id: str) -> Optional[int]:
        """Pickup has no travel: the ETA is just the preparation time."""
        if self._prep_time_estimator is None:
            return None
        return self._prep_time_estimator.estimate_minutes(business_config_id)
