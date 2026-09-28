"""Resolve an inbound channel thread to a Conversation.

Called by the channel driver (LangSmith/Studio now, WhatsApp later) BEFORE the
agent runs. The internal conversation id is a Rapidfood UUID; the external
thread identifier is stored alongside it so channels can be swapped without
touching the domain.
"""
from __future__ import annotations

from dataclasses import dataclass
from typing import Optional
from uuid import uuid4

from modules.conversation.application.ports.driven.conversation_repository import (
    ConversationRepositoryPort,
)
from modules.conversation.domain.models.conversation import Conversation


@dataclass(frozen=True, slots=True)
class ResolveConversationCommand:
    business_config_id: str
    channel: str
    external_thread_id: str
    client_id: Optional[str] = None


@dataclass(frozen=True, slots=True)
class ResolveConversationResult:
    conversation_id: str
    client_id: Optional[str]
    created: bool


class ResolveConversationForChannelUseCase:
    def __init__(self, conversation_repository: ConversationRepositoryPort) -> None:
        self._conversation_repository = conversation_repository

    def execute(self, command: ResolveConversationCommand) -> ResolveConversationResult:
        existing = self._conversation_repository.find_by_thread(
            command.business_config_id, command.channel, command.external_thread_id
        )
        if existing is not None:
            return ResolveConversationResult(
                conversation_id=existing.conversation_id,
                client_id=existing.client_id,
                created=False,
            )

        conversation = Conversation(
            conversation_id=str(uuid4()),
            channel=command.channel,
            external_thread_id=command.external_thread_id,
            business_config_id=command.business_config_id,
            client_id=command.client_id,
        )
        created = self._conversation_repository.create(conversation)
        conversation_id = (
            getattr(created, "conversation_id", None) or conversation.conversation_id
        )
        return ResolveConversationResult(
            conversation_id=conversation_id,
            client_id=command.client_id,
            created=True,
        )
