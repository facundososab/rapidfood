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
from modules.order.domain.errors.order_errors import DuplicateActiveOrderError
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
        existing = self._read_draft(command)
        if existing is not None:
            return GetOrCreateCurrentDraftResult(
                order_id=existing.id, status=existing.status.value, created=False
            )

        try:
            created = self._start_draft_order.execute(
                StartDraftOrderCommand(
                    client_id=command.client_id,
                    client_name=command.client_name,
                    business_config_id=command.business_config_id,
                    conversation_id=command.conversation_id,
                    origin=command.origin,
                )
            )
        except DuplicateActiveOrderError:
            # A parallel tool call won the race and created the draft first; the
            # partial unique index rejected ours. Reuse the winner instead of
            # failing: this is what keeps ONE active order per conversation.
            existing = self._read_draft(command)
            if existing is None:
                raise
            return GetOrCreateCurrentDraftResult(
                order_id=existing.id, status=existing.status.value, created=False
            )

        return GetOrCreateCurrentDraftResult(
            order_id=created.order_id, status=created.status, created=True
        )

    def _read_draft(self, command: GetOrCreateCurrentDraftCommand):
        existing = self._order_repo.list(
            OrderFilter(
                business_config_id=command.business_config_id,
                conversation_id=command.conversation_id,
                status=OrderState.DRAFT,
            )
        )
        return existing[0] if existing else None
