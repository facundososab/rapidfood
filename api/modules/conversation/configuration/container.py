from __future__ import annotations

from dataclasses import dataclass

from modules.conversation.application.use_cases.add_message import AddMessageUseCase
from modules.conversation.application.use_cases.get_or_create_conversation import GetOrCreateConversationUseCase
from modules.conversation.application.use_cases.list_messages import ListMessagesUseCase
from modules.conversation.application.use_cases.receive_message import ReceiveMessageUseCase
from modules.conversation.infrastructure.adapters.driven.clock import SystemClock
from modules.conversation.infrastructure.adapters.driven.intent.deterministic_intent_detector import (
    DeterministicIntentDetector,
)


@dataclass(slots=True)
class ConversationContainer:
    get_or_create_conversation_use_case: GetOrCreateConversationUseCase
    add_message_use_case: AddMessageUseCase
    list_messages_use_case: ListMessagesUseCase
    receive_message_use_case: ReceiveMessageUseCase


class _MemoryConversationRepository:
    def __init__(self):
        self._rows = {}

    def find_by_channel_identity(self, channel: str, channel_identity: str):
        return self._rows.get((channel, channel_identity))

    def create(self, conversation):
        self._rows[(conversation.channel, conversation.channel_identity)] = conversation
        return conversation

    def save_last_intent(self, conversation_id: str, last_intent):
        for key, conversation in self._rows.items():
            if conversation.conversation_id == conversation_id:
                conversation.last_intent = last_intent


class _MemoryMessageRepository:
    def __init__(self):
        self._messages = []

    def add(self, message):
        self._messages.append(message)
        return message

    def list_by_conversation(self, conversation_id: str):
        return [message for message in self._messages if message.conversation_id == conversation_id]


def build_container() -> ConversationContainer:
    conversation_repository = _MemoryConversationRepository()
    message_repository = _MemoryMessageRepository()
    clock = SystemClock()
    intent_detector = DeterministicIntentDetector()

    get_or_create = GetOrCreateConversationUseCase(conversation_repository)
    add_message = AddMessageUseCase(message_repository, clock)
    list_messages = ListMessagesUseCase(message_repository)
    receive_message = ReceiveMessageUseCase(conversation_repository, message_repository, intent_detector, clock)

    return ConversationContainer(
        get_or_create_conversation_use_case=get_or_create,
        add_message_use_case=add_message,
        list_messages_use_case=list_messages,
        receive_message_use_case=receive_message,
    )
