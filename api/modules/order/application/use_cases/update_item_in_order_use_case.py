"""Reopen-aware, idempotent update-item use case.

Updates an existing line identified by ``line_id``: quantity and optionally the
modifier/removed-ingredient configuration. Modifiers and removed ingredients are
re-validated against the catalog; prices are always recomputed by the backend.
"""
from __future__ import annotations

from modules.order.application.idempotency_key import build_idempotency_key
from modules.order.application.order_modification import prepare_order_for_modification
from modules.order.application.ports.driven.catalog_query import CatalogQuery
from modules.order.application.ports.driven.clock import ClockPort
from modules.order.application.ports.driven.idempotency import (
    IdempotentOrderMutationPort,
    OrderMutationContext,
)
from modules.order.application.ports.driver.update_item_in_order_port import (
    UpdateItemInOrderCommand,
    UpdateItemInOrderPort,
    UpdateItemInOrderResponse,
)
from modules.order.application.use_cases.add_line_use_case import (
    validate_modifiers,
    validate_removed_ingredients,
)
from modules.order.domain.errors.order_errors import InvalidLineError

_OPERATION_NAME = "update_item"


class UpdateItemInOrderUseCase(UpdateItemInOrderPort):
    def __init__(
        self,
        catalog_query: CatalogQuery,
        executor: IdempotentOrderMutationPort,
        clock: ClockPort,
    ) -> None:
        self._catalog_query = catalog_query
        self._executor = executor
        self._clock = clock

    def execute(self, command: UpdateItemInOrderCommand) -> UpdateItemInOrderResponse:
        idempotency_key = build_idempotency_key(
            business_config_id=command.business_config_id,
            conversation_id=command.conversation_id,
            external_message_id=command.external_message_id,
            operation_name=_OPERATION_NAME,
            args={
                "order_id": command.order_id,
                "line_id": command.line_id,
                "quantity": command.quantity,
                "modifier_option_ids": (
                    sorted(command.modifier_option_ids)
                    if command.modifier_option_ids is not None
                    else None
                ),
                "removed_ingredient_ids": (
                    sorted(command.removed_ingredient_ids)
                    if command.removed_ingredient_ids is not None
                    else None
                ),
            },
        )

        def mutate(ctx: OrderMutationContext) -> dict:
            order = ctx.order
            ctx.superseded_attempt_ids.extend(
                prepare_order_for_modification(order, ctx.attempts, self._clock.now())
            )

            line = next((l for l in order.lines if l.id == command.line_id), None)
            if line is None:
                raise InvalidLineError(f"Line {command.line_id} not found in order")

            if command.quantity is not None:
                if command.quantity <= 0:
                    raise InvalidLineError("Quantity must be greater than 0")
                line.quantity = command.quantity

            changes_configuration = (
                command.modifier_option_ids is not None
                or command.removed_ingredient_ids is not None
            )
            if changes_configuration:
                # Catalog read (in-process) to re-validate and reprice the line.
                context = self._catalog_query.get_variant_context(line.product_variant_id)
                if context is None or not context.is_sellable:
                    raise InvalidLineError("Variant is no longer available")

                if command.modifier_option_ids is not None:
                    line.modifiers = validate_modifiers(
                        command.modifier_option_ids, context, line.id
                    )
                if command.removed_ingredient_ids is not None:
                    line.removed_ingredients = validate_removed_ingredients(
                        command.removed_ingredient_ids, context, line.id
                    )

                option_lookup = {
                    opt.option_id: opt
                    for group in context.modifier_groups
                    for opt in group.options
                }
                modifier_total = sum(
                    option_lookup[m.modifier_option_id].price_delta
                    for m in line.modifiers
                    if m.modifier_option_id in option_lookup
                )
                line.unit_price = context.current_price + modifier_total

            # The unit price is recomputed on configuration changes; the line
            # subtotal always follows quantity × unit price.
            line.subtotal = line.unit_price * line.quantity

            order.mark_modified()

            return {
                "order_id": order.id,
                "line_id": line.id,
                "total_amount": str(order.total_amount),
                "line_count": len(order.lines),
                "version": order.version,
            }

        outcome = self._executor.execute(
            business_config_id=command.business_config_id,
            idempotency_key=idempotency_key,
            operation_name=_OPERATION_NAME,
            order_id=command.order_id,
            mutate=mutate,
        )

        return UpdateItemInOrderResponse(
            replayed=outcome.replayed,
            superseded_attempt_ids=outcome.superseded_attempt_ids,
            **outcome.result,
        )
