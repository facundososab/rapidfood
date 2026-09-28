"""Reopen-aware, idempotent remove-item use case.

Identifies the line by ``line_id`` (never by product/variant id: the same
variant may appear in several lines with different configurations).
"""
from __future__ import annotations

from modules.order.application.idempotency_key import build_idempotency_key
from modules.order.application.order_modification import prepare_order_for_modification
from modules.order.application.ports.driven.clock import ClockPort
from modules.order.application.ports.driven.idempotency import (
    IdempotentOrderMutationPort,
    OrderMutationContext,
)
from modules.order.application.ports.driver.remove_item_from_order_port import (
    RemoveItemFromOrderCommand,
    RemoveItemFromOrderPort,
    RemoveItemFromOrderResponse,
)
from modules.order.domain.errors.order_errors import InvalidLineError

_OPERATION_NAME = "remove_item"


class RemoveItemFromOrderUseCase(RemoveItemFromOrderPort):
    def __init__(
        self,
        executor: IdempotentOrderMutationPort,
        clock: ClockPort,
    ) -> None:
        self._executor = executor
        self._clock = clock

    def execute(self, command: RemoveItemFromOrderCommand) -> RemoveItemFromOrderResponse:
        idempotency_key = build_idempotency_key(
            business_config_id=command.business_config_id,
            conversation_id=command.conversation_id,
            external_message_id=command.external_message_id,
            operation_name=_OPERATION_NAME,
            args={"order_id": command.order_id, "line_id": command.line_id},
        )

        def mutate(ctx: OrderMutationContext) -> dict:
            order = ctx.order
            ctx.superseded_attempt_ids.extend(
                prepare_order_for_modification(order, ctx.attempts, self._clock.now())
            )

            if not any(line.id == command.line_id for line in order.lines):
                raise InvalidLineError(f"Line {command.line_id} not found in order")

            order.remove_line(command.line_id)
            return {
                "order_id": order.id,
                "line_count": len(order.lines),
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

        return RemoveItemFromOrderResponse(
            replayed=outcome.replayed,
            superseded_attempt_ids=outcome.superseded_attempt_ids,
            **outcome.result,
        )
