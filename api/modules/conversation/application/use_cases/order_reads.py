"""Conversation order reads (current order, summary, latest active)."""
from __future__ import annotations

from typing import Optional

from modules.conversation.domain.models.agent_execution_context import (
    AgentExecutionContext,
)
from modules.conversation.application.ports.driven.order_service import (
    CurrentOrderDTO,
    OrderServicePort,
    OrderStatusDTO,
    OrderSummaryDTO,
)
from modules.conversation.domain.errors import NoActiveOrderError


class GetCurrentOrderForConversationUseCase:
    def __init__(self, order_service: OrderServicePort) -> None:
        self._order_service = order_service

    def execute(self, context: AgentExecutionContext) -> CurrentOrderDTO:
        return self._order_service.get_current_order(
            context.business_configuration_id, context.conversation_id
        )


class GetLatestActiveOrderForConversationUseCase:
    def __init__(self, order_service: OrderServicePort) -> None:
        self._order_service = order_service

    def execute(self, context: AgentExecutionContext) -> Optional[OrderStatusDTO]:
        return self._order_service.get_latest_active_order(
            context.business_configuration_id,
            client_id=context.client_id,
            conversation_id=context.conversation_id,
        )


class GetOrderSummaryForConversationUseCase:
    """Summary of the order the conversation is working on.

    The order id is resolved from the trusted context, never supplied by the
    model, so the agent can never read another conversation's order.
    """

    def __init__(self, order_service: OrderServicePort) -> None:
        self._order_service = order_service

    def execute(self, context: AgentExecutionContext) -> OrderSummaryDTO:
        current = self._order_service.get_current_order(
            context.business_configuration_id, context.conversation_id
        )
        if not current.found or current.order_id is None:
            raise NoActiveOrderError("La conversación todavía no tiene un pedido.")
        return self._order_service.get_order_summary(current.order_id)
