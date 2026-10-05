"""Resolve an inbound channel thread to a Conversation.

Called by the channel driver (LangSmith/Studio now, WhatsApp later) BEFORE the
agent runs. The internal conversation id is a Rapidfood UUID; the external
thread identifier is stored alongside it so channels can be swapped without
touching the domain.
"""
from __future__ import annotations

import logging
from dataclasses import dataclass
from typing import Optional
from uuid import uuid4

from modules.conversation.application.ports.driven.conversation_repository import (
    ConversationRepositoryPort,
)
from modules.conversation.domain.models.conversation import Conversation

logger = logging.getLogger(__name__)


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
    # A human took over: the channel driver must NOT run the agent for this thread.
    agent_paused: bool = False


class ResolveConversationForChannelUseCase:
    def __init__(self, conversation_repository: ConversationRepositoryPort) -> None:
        self._conversation_repository = conversation_repository

    def execute(self, command: ResolveConversationCommand) -> ResolveConversationResult:
        existing = self._conversation_repository.find_by_thread(
            command.business_config_id, command.channel, command.external_thread_id
        )
        if existing is not None:
            client_id = existing.client_id
            # Link the customer the first time we can resolve them (a later turn
            # may learn the phone/name); never overwrite an existing link.
            if command.client_id and not client_id:
                try:
                    self._conversation_repository.set_client_id(
                        existing.conversation_id, command.client_id
                    )
                    client_id = command.client_id
                except Exception:  # linking is best-effort
                    logger.exception(
                        "Could not link client %s to conversation %s",
                        command.client_id,
                        existing.conversation_id,
                    )
            return ResolveConversationResult(
                conversation_id=existing.conversation_id,
                client_id=client_id,
                created=False,
                agent_paused=bool(getattr(existing, "agent_paused", False)),
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
