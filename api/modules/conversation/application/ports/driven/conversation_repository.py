from __future__ import annotations

from typing import Protocol, runtime_checkable

from modules.conversation.domain.models.conversation import Conversation
from modules.conversation.domain.value_objects import ConversationRecord, DetectedIntent


@runtime_checkable
class ConversationRepositoryPort(Protocol):
    def find_by_channel_identity(self, channel: str, channel_identity: str) -> ConversationRecord | None: ...

    def create(self, conversation: Conversation) -> ConversationRecord | Conversation: ...

    def save_last_intent(self, conversation_id: str, last_intent: DetectedIntent | None): ...
