"""Driven port: outbound messages to the customer's channel.

The conversation module produces messages the business sends to the customer
(the agent's replies, and proactive notifications like "your order is paid").
This port is the SEND-ONLY boundary to the actual channel (WhatsApp, etc.): it
delivers bytes and never persists. Persistence is the caller's responsibility, so
reply paths (already stored by their use case) never duplicate the message.
"""
from __future__ import annotations

from dataclasses import dataclass
from typing import Optional, Protocol, runtime_checkable


@dataclass(frozen=True, slots=True)
class OutboundMessage:
    conversation_id: str
    channel: str
    # External channel identity of the recipient (WhatsApp phone, thread id, ...).
    destination: Optional[str]
    content: str


@runtime_checkable
class OutboundMessagePort(Protocol):
    def send(self, message: OutboundMessage) -> None: ...
