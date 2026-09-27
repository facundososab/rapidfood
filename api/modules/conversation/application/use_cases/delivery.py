"""Delivery quote for the agent.

Setting delivery lives in ``order_mutations`` (
``SetDeliveryForConversationOrderUseCase``): the order module quotes the address
and only stores a delivery when it is available, so conversation never computes
shipping.
"""
from __future__ import annotations

from modules.conversation.application.address_defaults import (
    complete_address,
    require_deliverable_address,
)
from modules.conversation.application.ports.driven.business_service import (
    BusinessServicePort,
)
from modules.conversation.application.ports.driven.delivery_service import (
    DeliveryQuoteDTO,
    DeliveryServicePort,
)
from modules.conversation.application.ports.driver.agent_commands import (
    QuoteDeliveryQuery,
)
from modules.conversation.domain.models.agent_execution_context import (
    AgentExecutionContext,
)


class QuoteDeliveryForConversationUseCase:
    """Answer "do you deliver to X?" — works with NO order at all."""

    def __init__(
        self,
        delivery_service: DeliveryServicePort,
        business_service: BusinessServicePort | None = None,
    ) -> None:
        self._delivery_service = delivery_service
        self._business_service = business_service

    def execute(
        self, query: QuoteDeliveryQuery, context: AgentExecutionContext
    ) -> DeliveryQuoteDTO:
        # Street + number are enough: the city/province are the restaurant's.
        defaults = (
            self._business_service.get_address(context.business_configuration_id)
            if self._business_service is not None
            else None
        )
        address = require_deliverable_address(complete_address(query.address, defaults))
        return self._delivery_service.quote_delivery(
            context.business_configuration_id, address.as_dict()
        )
