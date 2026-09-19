from __future__ import annotations

from dataclasses import dataclass
from enum import StrEnum


class MessageRole(StrEnum):
    USER = "USER"
    AGENT = "AGENT"
    SYSTEM = "SYSTEM"


class MessageAuthor(StrEnum):
    """Who actually wrote a message.

    `role` is the LLM-facing role (USER = the customer, AGENT = the business
    side); `author` distinguishes an automated agent reply from a human operator
    speaking on the business side. Both share the AGENT role so the model sees
    operator messages as its own past turns.
    """

    CLIENT = "CLIENT"
    AGENT = "AGENT"
    OPERATOR = "OPERATOR"


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
    external_thread_id: str | None = None
    business_config_id: str | None = None
    agent_paused: bool = False


def coerce_enum(value, enum_cls, field_name: str):
    if value is None or isinstance(value, enum_cls):
        return value
    try:
        return enum_cls(value)
    except Exception as exc:  # pragma: no cover - defensive
        raise ValueError(f"Invalid {field_name}: {value!r}") from exc
