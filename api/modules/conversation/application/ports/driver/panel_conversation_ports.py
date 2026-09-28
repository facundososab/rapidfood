"""Driver DTOs for the panel's conversation chat."""
from __future__ import annotations

from dataclasses import dataclass, field
from typing import Optional, Tuple


@dataclass(frozen=True, slots=True)
class ConversationMessageDTO:
    message_id: str
    role: str
    content: str
    created_at: Optional[str] = None
    # CLIENT | AGENT | OPERATOR - who actually wrote the message.
    author: Optional[str] = None


@dataclass(frozen=True, slots=True)
class ConversationSummaryDTO:
    conversation_id: str
    channel: str
    external_thread_id: Optional[str]
    client_id: Optional[str]
    agent_paused: bool
    message_count: int
    client_name: Optional[str] = None
    client_phone: Optional[str] = None
    last_message: Optional[str] = None
    last_role: Optional[str] = None
    last_at: Optional[str] = None


@dataclass(frozen=True, slots=True)
class ConversationDetailDTO:
    conversation_id: str
    channel: str
    external_thread_id: Optional[str]
    client_id: Optional[str]
    agent_paused: bool
    messages: Tuple[ConversationMessageDTO, ...] = field(default_factory=tuple)
    client_name: Optional[str] = None
    client_phone: Optional[str] = None
    last_intent: Optional[str] = None
    overall_sentiment: Optional[str] = None


@dataclass(frozen=True, slots=True)
class ClientReplyResultDTO:
    """Result of the operator typing as the customer."""

    conversation_id: str
    paused: bool
    response: Optional[str]
    detail: ConversationDetailDTO
