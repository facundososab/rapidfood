"""Driver port: deliver a message to a conversation's channel.

Channel-neutral: callers (the inbound webhook, the panel, proactive
notifications) ask "deliver this content to this conversation", and the outbound
adapter resolves the channel and credentials. Send-only — persistence belongs to
the caller.
"""
from __future__ import annotations

from dataclasses import dataclass
from typing import Protocol


@dataclass(frozen=True, slots=True)
class SendConversationMessageCommand:
    conversation_id: str
    content: str


class SendConversationMessagePort(Protocol):
    def execute(self, command: SendConversationMessageCommand) -> bool:
        """Deliver to the conversation's channel (no persistence). False if N/A."""
        ...
