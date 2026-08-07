from __future__ import annotations

from dataclasses import dataclass

from api.modules.conversation.domain.value_objects import DetectedIntent, MessageRole, MessageStatus, Sentiment


@dataclass(frozen=True, slots=True)
class GetOrCreateConversationCommand:
    channel: str
    channel_identity: str
    client_id: str | None = None


@dataclass(frozen=True, slots=True)
class AddMessageCommand:
    message_id: str
    conversation_id: str
    role: MessageRole
    content: str
    detected_intent: DetectedIntent | None = None
    sentiment: Sentiment | None = None
    status: MessageStatus = MessageStatus.RECEIVED


@dataclass(frozen=True, slots=True)
class ListMessagesQuery:
    conversation_id: str


@dataclass(frozen=True, slots=True)
class ReceiveMessageCommand:
    channel: str
    channel_identity: str
    content: str
    external_message_id: str | None = None
