from __future__ import annotations

from typing import Protocol, runtime_checkable

from modules.conversation.domain.models.message import Message


@runtime_checkable
class MessageRepositoryPort(Protocol):
    def add(self, message: Message) -> Message: ...

    def find_by_id(self, message_id: str) -> Message | None: ...

    def list_by_conversation(self, conversation_id: str) -> list[Message]: ...
