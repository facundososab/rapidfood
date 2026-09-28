"""Resolve the latest active order for the current business (and client).

The backend decides which order the customer is asking about; the caller never
lists orders and guesses.
"""
from __future__ import annotations

from typing import Optional

from modules.order.application.ports.driven.order_repository import (
    OrderFilter,
    OrderRepository,
)
from modules.order.application.ports.driver.get_latest_active_order_port import (
    GetLatestActiveOrderPort,
    GetLatestActiveOrderQuery,
)
from modules.order.domain.models.order import Order
from modules.order.domain.models.order_state import OrderState

# Orders currently being handled (not drafts, not finished/cancelled).
ACTIVE_STATES = (
    OrderState.PENDING,
    OrderState.PAID,
    OrderState.CONFIRMED,
    OrderState.IN_PREPARATION,
    OrderState.READY,
)


class GetLatestActiveOrderUseCase(GetLatestActiveOrderPort):
    def __init__(self, order_repo: OrderRepository) -> None:
        self._order_repo = order_repo

    def execute(self, query: GetLatestActiveOrderQuery) -> Optional[Order]:
        order_filter = OrderFilter(
            business_config_id=query.business_config_id,
            status_in=list(ACTIVE_STATES),
        )
        # Prefer the client scope when known; otherwise fall back to the
        # conversation so an unidentified agent order can still be found.
        if query.client_id:
            order_filter.client_id = query.client_id
        elif query.conversation_id:
            order_filter.conversation_id = query.conversation_id

        orders = self._order_repo.list(order_filter)
        return orders[0] if orders else None
