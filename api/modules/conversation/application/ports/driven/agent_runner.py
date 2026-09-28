"""Driven port: the conversational agent runner.

Implemented by the LangChain/LangGraph driver adapter. The application only
knows "given a message, the history and a trusted context, produce a reply" —
it never imports a model framework.
"""
from __future__ import annotations

from dataclasses import dataclass
from typing import Protocol, Tuple

from modules.conversation.domain.models.agent_execution_context import (
    AgentExecutionContext,
)
from modules.conversation.domain.value_objects import MessageRole


@dataclass(frozen=True, slots=True)
class AgentTurn:
    message: str
    context: AgentExecutionContext
    # Previous turns as (role, content), where role is the DOMAIN role the
    # message was stored with (MessageRole: USER / AGENT / SYSTEM) - never the
    # framework's own vocabulary. Mapping it to model messages is the adapter's
    # job, and it must be exhaustive: a role silently falling back to "human"
    # feeds the agent its own words back as the customer's.
    history: Tuple[Tuple[MessageRole, str], ...] = ()


class AgentRunnerPort(Protocol):
    def run(self, turn: AgentTurn) -> str: ...
