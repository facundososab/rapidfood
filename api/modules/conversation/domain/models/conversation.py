from __future__ import annotations

from dataclasses import dataclass

from modules.conversation.domain.errors import ConversationValidationError
from modules.conversation.domain.value_objects import DetectedIntent, Sentiment, coerce_enum


@dataclass(slots=True)
class Conversation:
    conversation_id: str
    channel: str
    channel_identity: str | None = None
    overall_sentiment: Sentiment | None = None
    last_intent: DetectedIntent | None = None
    client_id: str | None = None

    def __post_init__(self) -> None:
        if not self.conversation_id:
            raise ConversationValidationError("conversation_id is required")
        if not self.channel:
            raise ConversationValidationError("channel is required")
        if self.channel_identity is not None and not self.channel_identity:
            raise ConversationValidationError("channel_identity cannot be empty")
        try:
            self.overall_sentiment = coerce_enum(self.overall_sentiment, Sentiment, "overall_sentiment")
            self.last_intent = coerce_enum(self.last_intent, DetectedIntent, "last_intent")
        except ValueError as exc:
            raise ConversationValidationError(str(exc)) from exc
