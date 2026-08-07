from __future__ import annotations

from api.modules.conversation.application.ports.driver.conversation_commands import AddMessageCommand
from api.modules.conversation.application.ports.driver.conversation_responses import AddMessageResult, MessageDTO
from api.modules.conversation.application.ports.driven.clock import ClockPort
from api.modules.conversation.application.ports.driven.message_repository import MessageRepositoryPort
from api.modules.conversation.domain.models.message import Message


class AddMessageUseCase:
    def __init__(self, message_repository: MessageRepositoryPort, clock: ClockPort):
        self._message_repository = message_repository
        self._clock = clock

    def execute(self, command: AddMessageCommand) -> AddMessageResult:
        message = Message(
            message_id=command.message_id,
            conversation_id=command.conversation_id,
            role=command.role,
            content=command.content,
            detected_intent=command.detected_intent,
            sentiment=command.sentiment,
            status=command.status,
            created_at=self._clock.now(),
        )
        saved = self._message_repository.add(message)
        return AddMessageResult(message=_to_message_dto(saved))


def _to_message_dto(message: Message) -> MessageDTO:
    return MessageDTO(
        message_id=message.message_id,
        conversation_id=message.conversation_id,
        role=message.role,
        content=message.content,
        detected_intent=message.detected_intent,
        sentiment=message.sentiment,
        status=message.status,
        created_at=message.created_at,
    )
