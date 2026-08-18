from __future__ import annotations

from dataclasses import dataclass
from datetime import datetime

from modules.conversation.domain.value_objects import DetectedIntent, MessageRole, MessageStatus, Sentiment


@dataclass(frozen=True, slots=True)
class ConversationDTO:
    conversation_id: str
    channel: str
    channel_identity: str | None = None
    client_id: str | None = None
    overall_sentiment: Sentiment | None = None
    last_intent: DetectedIntent | None = None


@dataclass(frozen=True, slots=True)
class MessageDTO:
    message_id: str
    conversation_id: str
    role: MessageRole
    content: str
    detected_intent: DetectedIntent | None = None
    sentiment: Sentiment | None = None
    status: MessageStatus = MessageStatus.RECEIVED
    created_at: datetime | None = None


@dataclass(frozen=True, slots=True)
class GetOrCreateConversationResult:
    conversation: ConversationDTO
    created: bool

    @property
    def conversation_id(self) -> str:
        return self.conversation.conversation_id

    @property
    def channel(self) -> str:
        return self.conversation.channel


@dataclass(frozen=True, slots=True)
class AddMessageResult:
    message: MessageDTO

    @property
    def message_id(self) -> str:
        return self.message.message_id

    @property
    def conversation_id(self) -> str:
        return self.message.conversation_id


@dataclass(frozen=True, slots=True)
class ListMessagesResult:
    conversation_id: str
    messages: list[MessageDTO]


@dataclass(frozen=True, slots=True)
class ReceiveMessageResult:
    conversation_id: str
    user_message_id: str
    agent_message_id: str
    intent: DetectedIntent
    response: str
