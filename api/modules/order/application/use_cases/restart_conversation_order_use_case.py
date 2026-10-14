"""Close a conversation's in-progress order and open a fresh draft.

A conversation is long-lived (a WhatsApp thread never changes), so a DRAFT or an
unpaid PENDING order left behind by an earlier session would otherwise be reused
by the next one. When the channel signals a new session, this use case closes the
stale order and opens a clean draft for the new one.

Only pre-confirmation orders are touched (DRAFT / PENDING): an order already
accepted or in preparation is real work in flight and is never disturbed.
Calling it is idempotent-ish in the sense that a conversation with no active
order is a no-op (nothing to close, nothing to open), so the caller can invoke it
on every new-session boundary.
"""
from __future__ import annotations

from modules.order.application.ports.driven.order_repository import (
    OrderFilter,
    OrderRepository,
)
from modules.order.application.ports.driver.restart_conversation_order_port import (
    RestartConversationOrderCommand,
    RestartConversationOrderPort,
    RestartConversationOrderResponse,
)
from modules.order.application.ports.driver.start_draft_order_ports import (
    StartDraftOrderCommand,
    StartDraftOrderPort,
)
from modules.order.domain.errors.order_errors import DuplicateActiveOrderError
from modules.order.domain.models.order_origin import OrderOrigin
from modules.order.domain.models.order_state import OrderState

# States that belong to an unfinished ordering session. Once an order leaves
# these, it is committed work and must not be closed behind the customer's back.
_SESSION_STATES = (OrderState.DRAFT, OrderState.PENDING)


class RestartConversationOrderUseCase(RestartConversationOrderPort):
    def __init__(
        self,
        order_repo: OrderRepository,
        start_draft_order: StartDraftOrderPort,
    ) -> None:
        self._order_repo = order_repo
        self._start_draft_order = start_draft_order

    def execute(
        self, command: RestartConversationOrderCommand
    ) -> RestartConversationOrderResponse:
        active = self._active_order(command)
        if active is None:
            return RestartConversationOrderResponse(
                previous_order_id=None, order_id=None, created=False
            )

        active.status = OrderState.CANCELLED
        self._order_repo.save(active)

        try:
            created = self._start_draft_order.execute(
                StartDraftOrderCommand(
                    business_config_id=command.business_config_id,
                    conversation_id=command.conversation_id,
                    client_id=command.client_id,
                    client_name=command.client_name,
                    origin=OrderOrigin.AGENT.value,
                )
            )
        except DuplicateActiveOrderError:
            # A concurrent turn already opened the new draft: reuse it instead of
            # failing (the partial unique index keeps ONE active order).
            winner = self._active_order(command)
            if winner is None:
                raise
            return RestartConversationOrderResponse(
                previous_order_id=active.id,
                order_id=winner.id,
                created=False,
            )

        return RestartConversationOrderResponse(
            previous_order_id=active.id,
            order_id=created.order_id,
            created=True,
        )

    def _active_order(self, command: RestartConversationOrderCommand):
        for status in _SESSION_STATES:
            found = self._order_repo.list(
                OrderFilter(
                    business_config_id=command.business_config_id,
                    conversation_id=command.conversation_id,
                    status=status,
                )
            )
            if found:
                return found[0]
        return None
