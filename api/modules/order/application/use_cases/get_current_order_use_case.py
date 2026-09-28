"""Pure read of the order a conversation is currently working on.

Returns the DRAFT if there is one, else the PENDING order (which a mutation
could reopen), else the latest order of the conversation (useful for status
questions). It NEVER mutates and NEVER creates an order.
"""
from __future__ import annotations

from modules.order.application.order_modification import modification_readiness
from modules.order.application.ports.driven.order_repository import (
    OrderFilter,
    OrderRepository,
)
from modules.order.application.ports.driven.payment_attempt_query import (
    PaymentAttemptQueryPort,
)
from modules.order.application.ports.driver.get_current_order_port import (
    CurrentOrderResult,
    GetCurrentOrderPort,
    GetCurrentOrderQuery,
)
from modules.order.domain.models.order_state import OrderState


class GetCurrentOrderUseCase(GetCurrentOrderPort):
    def __init__(
        self,
        order_repo: OrderRepository,
        attempts: PaymentAttemptQueryPort,
    ) -> None:
        self._order_repo = order_repo
        self._attempts = attempts

    def execute(self, query: GetCurrentOrderQuery) -> CurrentOrderResult:
        scope = dict(
            business_config_id=query.business_config_id,
            conversation_id=query.conversation_id,
        )

        order = self._first(OrderFilter(status=OrderState.DRAFT, **scope))
        if order is None:
            order = self._first(OrderFilter(status=OrderState.PENDING, **scope))
        if order is None:
            order = self._first(OrderFilter(**scope))

        if order is None:
            return CurrentOrderResult(
                found=False, order=None, editable=True, requires_new_order=False
            )

        readiness = modification_readiness(order, self._attempts)
        return CurrentOrderResult(
            found=True,
            order=order,
            editable=readiness.editable,
            requires_reopen=readiness.requires_reopen,
            requires_new_order=readiness.requires_new_order,
        )

    def _first(self, order_filter: OrderFilter):
        orders = self._order_repo.list(order_filter)
        return orders[0] if orders else None
