from __future__ import annotations

from modules.conversation.application.ports.driver.conversation_commands import ListMessagesQuery
from modules.conversation.application.ports.driver.conversation_responses import ListMessagesResult
from modules.conversation.application.ports.driven.message_repository import MessageRepositoryPort
from modules.conversation.application.use_cases.add_message import _to_message_dto


class ListMessagesUseCase:
    def __init__(self, message_repository: MessageRepositoryPort):
        self._message_repository = message_repository

    def execute(self, query: ListMessagesQuery) -> ListMessagesResult:
        messages = sorted(
            self._message_repository.list_by_conversation(query.conversation_id),
            key=lambda message: (message.created_at is None, message.created_at, message.message_id),
        )
        return ListMessagesResult(
            conversation_id=query.conversation_id,
            messages=[_to_message_dto(message) for message in messages],
        )
