from __future__ import annotations

from dataclasses import dataclass
from datetime import datetime

from api.modules.conversation.domain.errors import MessageValidationError
from api.modules.conversation.domain.value_objects import (
    DetectedIntent,
    MessageRole,
    MessageStatus,
    Sentiment,
    coerce_enum,
)


@dataclass(slots=True)
class Message:
    message_id: str
    conversation_id: str
    role: MessageRole
    content: str
    detected_intent: DetectedIntent | None = None
    sentiment: Sentiment | None = None
    status: MessageStatus = MessageStatus.RECEIVED
    created_at: datetime | None = None

    def __post_init__(self) -> None:
        if not self.message_id:
            raise MessageValidationError("message_id is required")
        if not self.conversation_id:
            raise MessageValidationError("conversation_id is required")
        if not self.content:
            raise MessageValidationError("content is required")
        try:
            self.role = coerce_enum(self.role, MessageRole, "role")
            self.status = coerce_enum(self.status, MessageStatus, "status")
            self.detected_intent = coerce_enum(self.detected_intent, DetectedIntent, "detected_intent")
            self.sentiment = coerce_enum(self.sentiment, Sentiment, "sentiment")
        except ValueError as exc:
            raise MessageValidationError(str(exc)) from exc
