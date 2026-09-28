"""Trusted execution context for the conversational agent (domain value object).

Resolved by the channel driver BEFORE any tool runs (from the thread + business
+ client), and injected into every use case. The model never supplies these
values, so it can never switch restaurant, conversation or client.

Framework-free on purpose: it lives in the domain so both the application and
the infrastructure adapters can depend on it without crossing layers.
"""
from __future__ import annotations

from dataclasses import dataclass
from typing import Optional


@dataclass(frozen=True, slots=True)
class AgentExecutionContext:
    business_configuration_id: str
    conversation_id: str
    channel: str
    client_id: Optional[str] = None
    external_thread_id: Optional[str] = None
    # Per-ingress message identity, stable across retries. Used for the
    # idempotency key of write operations; never the tracing run id.
    external_message_id: Optional[str] = None

    def __post_init__(self) -> None:
        if not self.business_configuration_id:
            raise ValueError("business_configuration_id is required")
        if not self.conversation_id:
            raise ValueError("conversation_id is required")
        if not self.channel:
            raise ValueError("channel is required")
