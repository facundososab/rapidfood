from __future__ import annotations

from dataclasses import asdict
from uuid import uuid4

from modules.conversation.application.ports.driver.conversation_commands import GetOrCreateConversationCommand
from modules.conversation.application.ports.driver.conversation_responses import (
    ConversationDTO,
    GetOrCreateConversationResult,
)
from modules.conversation.application.ports.driven.conversation_repository import ConversationRepositoryPort
from modules.conversation.domain.models.conversation import Conversation


class GetOrCreateConversationUseCase:
    def __init__(self, conversation_repository: ConversationRepositoryPort):
        self._conversation_repository = conversation_repository

    def execute(self, command: GetOrCreateConversationCommand) -> GetOrCreateConversationResult:
        existing = self._conversation_repository.find_by_channel_identity(command.channel, command.channel_identity)
        if existing is not None:
            conversation_dto = _to_conversation_dto(existing, command.channel_identity)
            return GetOrCreateConversationResult(conversation=conversation_dto, created=False)

        conversation = Conversation(
            conversation_id=str(uuid4()),
            channel=command.channel,
            channel_identity=command.channel_identity,
            client_id=command.client_id,
        )
        created = self._conversation_repository.create(conversation)
        conversation_dto = _to_conversation_dto(created, command.channel_identity)
        return GetOrCreateConversationResult(conversation=conversation_dto, created=True)


def _to_conversation_dto(conversation, channel_identity: str | None = None) -> ConversationDTO:
    if hasattr(conversation, "conversation_id"):
        return ConversationDTO(
            conversation_id=getattr(conversation, "conversation_id"),
            channel=getattr(conversation, "channel"),
            channel_identity=getattr(conversation, "channel_identity", channel_identity),
            client_id=getattr(conversation, "client_id", None),
            overall_sentiment=getattr(conversation, "overall_sentiment", None),
            last_intent=getattr(conversation, "last_intent", None),
        )
    return ConversationDTO(**conversation)
