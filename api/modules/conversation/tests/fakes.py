"""In-memory repositories for conversation tests (no DB)."""
from __future__ import annotations

from modules.conversation.domain.models.conversation import Conversation
from modules.conversation.domain.value_objects import ConversationRecord


class InMemoryConversationRepository:
    def __init__(self) -> None:
        self.rows: dict[tuple[str, str, str], Conversation] = {}

    def find_by_thread(self, business_config_id, channel, external_thread_id):
        return self.rows.get((business_config_id, channel, external_thread_id))

    def get_by_id(self, conversation_id):
        for conversation in self.rows.values():
            if conversation.conversation_id == conversation_id:
                return conversation
        return None

    def list_conversations(self):
        return list(self.rows.values())

    def set_agent_paused(self, conversation_id, paused):
        conversation = self.get_by_id(conversation_id)
        if conversation is not None:
            conversation.agent_paused = bool(paused)

    def find_by_channel_identity(self, channel, channel_identity):
        for conversation in self.rows.values():
            if conversation.channel == channel and conversation.client_id is None:
                return conversation
        return None

    def create(self, conversation: Conversation):
        self.rows[
            (
                conversation.business_config_id,
                conversation.channel,
                conversation.external_thread_id,
            )
        ] = conversation
        return conversation

    def save_last_intent(self, conversation_id, last_intent):
        for conversation in self.rows.values():
            if conversation.conversation_id == conversation_id:
                conversation.last_intent = last_intent


class InMemoryMessageRepository:
    def __init__(self) -> None:
        self.messages: list = []

    def add(self, message):
        self.messages.append(message)
        return message

    def list_by_conversation(self, conversation_id):
        return [m for m in self.messages if m.conversation_id == conversation_id]
