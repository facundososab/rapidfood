"""Idempotent get-or-create of the current DRAFT for a conversation.

Reuses the existing ``StartDraftOrderUseCase`` for creation: it is a real read
plus, only when there is no draft, the normal creation flow. This keeps a single
active draft per conversation/business without duplicating creation logic.
"""
from __future__ import annotations

from modules.order.application.ports.driven.order_repository import (
    OrderFilter,
    OrderRepository,
)
from modules.order.application.ports.driver.get_or_create_current_draft_port import (
    GetOrCreateCurrentDraftCommand,
    GetOrCreateCurrentDraftPort,
    GetOrCreateCurrentDraftResult,
)
from modules.order.application.ports.driver.start_draft_order_ports import (
    StartDraftOrderCommand,
    StartDraftOrderPort,
)
from modules.order.domain.models.order_state import OrderState


class GetOrCreateCurrentDraftUseCase(GetOrCreateCurrentDraftPort):
    def __init__(
        self,
        order_repo: OrderRepository,
        start_draft_order: StartDraftOrderPort,
    ) -> None:
        self._order_repo = order_repo
        self._start_draft_order = start_draft_order

    def execute(
        self, command: GetOrCreateCurrentDraftCommand
    ) -> GetOrCreateCurrentDraftResult:
        existing = self._order_repo.list(
            OrderFilter(
                business_config_id=command.business_config_id,
                conversation_id=command.conversation_id,
                status=OrderState.DRAFT,
            )
        )
        if existing:
            draft = existing[0]
            return GetOrCreateCurrentDraftResult(
                order_id=draft.id, status=draft.status.value, created=False
            )

        created = self._start_draft_order.execute(
            StartDraftOrderCommand(
                client_id=command.client_id,
                client_name=command.client_name,
                business_config_id=command.business_config_id,
                conversation_id=command.conversation_id,
                origin=command.origin,
            )
        )
        return GetOrCreateCurrentDraftResult(
            order_id=created.order_id, status=created.status, created=True
        )
