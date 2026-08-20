from __future__ import annotations

from dataclasses import dataclass
from enum import StrEnum


class MessageRole(StrEnum):
    USER = "USER"
    AGENT = "AGENT"
    SYSTEM = "SYSTEM"


class MessageStatus(StrEnum):
    RECEIVED = "RECEIVED"
    PROCESSED = "PROCESSED"
    FAILED = "FAILED"


class DetectedIntent(StrEnum):
    START_ORDER = "START_ORDER"
    MODIFY_ORDER = "MODIFY_ORDER"
    CONFIRM_ORDER = "CONFIRM_ORDER"
    QUERY_DRAFT = "QUERY_DRAFT"
    QUERY_ORDER = "QUERY_ORDER"
    UNKNOWN = "UNKNOWN"


class Sentiment(StrEnum):
    POSITIVE = "positive"
    NEUTRAL = "neutral"
    NEGATIVE = "negative"


@dataclass(frozen=True, slots=True)
class ConversationRecord:
    conversation_id: str
    channel: str
    channel_identity: str | None = None
    client_id: str | None = None
    last_intent: DetectedIntent | None = None
    overall_sentiment: Sentiment | None = None


def coerce_enum(value, enum_cls, field_name: str):
    if value is None or isinstance(value, enum_cls):
        return value
    try:
        return enum_cls(value)
    except Exception as exc:  # pragma: no cover - defensive
        raise ValueError(f"Invalid {field_name}: {value!r}") from exc
