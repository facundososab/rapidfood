"""Reopen-aware, idempotent add-item use case.

Orchestration:
  1. validate the variant against the catalog (outside the transaction),
  2. derive a channel-neutral idempotency key for the ingress message,
  3. inside ONE transaction: reopen the order when allowed (PENDING ONLINE
     without a current approved payment), add the line, bump the version and
     store the operation result.

Reopen and line validation reuse the same rules as the plain add-line use case.
"""
from __future__ import annotations

from uuid import uuid4

from modules.order.application.idempotency_key import build_idempotency_key
from modules.order.application.order_modification import prepare_order_for_modification
from modules.order.application.ports.driven.catalog_query import CatalogQuery
from modules.order.application.ports.driven.clock import ClockPort
from modules.order.application.ports.driven.idempotency import (
    IdempotentOrderMutationPort,
    OrderMutationContext,
)
from modules.order.application.ports.driver.add_item_to_order_port import (
    AddItemToOrderCommand,
    AddItemToOrderPort,
    AddItemToOrderResponse,
)
from modules.order.application.use_cases.add_line_use_case import (
    validate_modifiers,
    validate_removed_ingredients,
)
from modules.order.domain.errors.order_errors import InvalidLineError
from modules.order.domain.models.order_line import OrderLine

_OPERATION_NAME = "add_item"


class AddItemToOrderUseCase(AddItemToOrderPort):
    def __init__(
        self,
        catalog_query: CatalogQuery,
        executor: IdempotentOrderMutationPort,
        clock: ClockPort,
    ) -> None:
        self._catalog_query = catalog_query
        self._executor = executor
        self._clock = clock

    def execute(self, command: AddItemToOrderCommand) -> AddItemToOrderResponse:
        context = self._catalog_query.get_variant_context(command.product_variant_id)
        if context is None:
            raise InvalidLineError(f"Variant {command.product_variant_id} not found")
        if not context.is_sellable:
            raise InvalidLineError(
                f"Variant {context.variant_name} of product {context.product_name} is not available"
            )

        idempotency_key = build_idempotency_key(
            business_config_id=command.business_config_id,
            conversation_id=command.conversation_id,
            external_message_id=command.external_message_id,
            operation_name=_OPERATION_NAME,
            args={
                "order_id": command.order_id,
                "product_variant_id": command.product_variant_id,
                "quantity": command.quantity,
                "modifier_option_ids": sorted(command.modifier_option_ids),
                "removed_ingredient_ids": sorted(command.removed_ingredient_ids),
            },
        )

        def mutate(ctx: OrderMutationContext) -> dict:
            order = ctx.order
            ctx.superseded_attempt_ids.extend(
                prepare_order_for_modification(order, ctx.attempts, self._clock.now())
            )

            line_id = str(uuid4())
            removed_ingredients = validate_removed_ingredients(
                command.removed_ingredient_ids, context, line_id
            )
            modifiers = validate_modifiers(
                command.modifier_option_ids, context, line_id
            )

            option_lookup = {
                opt.option_id: opt
                for group in context.modifier_groups
                for opt in group.options
            }
            modifier_total = sum(
                option_lookup[option_id].price_delta
                for option_id in command.modifier_option_ids
            )
            unit_price = context.current_price + modifier_total
            subtotal = unit_price * command.quantity

            order.add_line(
                OrderLine(
                    id=line_id,
                    order_id=order.id,
                    product_variant_id=context.variant_id,
                    quantity=command.quantity,
                    unit_price=unit_price,
                    subtotal=subtotal,
                    modifiers=modifiers,
                    removed_ingredients=removed_ingredients,
                )
            )

            return {
                "order_id": order.id,
                "line_id": line_id,
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

        return AddItemToOrderResponse(
            replayed=outcome.replayed,
            superseded_attempt_ids=outcome.superseded_attempt_ids,
            **outcome.result,
        )
