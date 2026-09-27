from __future__ import annotations

from dataclasses import dataclass
from datetime import datetime

from modules.conversation.domain.errors import MessageValidationError
from modules.conversation.domain.value_objects import (
    DetectedIntent,
    MessageAuthor,
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
    # Who wrote it. Defaults from `role` (USER -> CLIENT, otherwise AGENT); an
    # operator takeover sets OPERATOR explicitly.
    author: MessageAuthor | None = None

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
            self.author = coerce_enum(self.author, MessageAuthor, "author")
        except ValueError as exc:
            raise MessageValidationError(str(exc)) from exc
        if self.author is None:
            self.author = (
                MessageAuthor.CLIENT
                if self.role is MessageRole.USER
                else MessageAuthor.AGENT
            )
        if self.author is MessageAuthor.CLIENT and self.role is not MessageRole.USER:
            raise MessageValidationError("a CLIENT message must have the USER role")
