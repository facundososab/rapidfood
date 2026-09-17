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


@dataclass(frozen=True, slots=True)
class AgentTurn:
    message: str
    context: AgentExecutionContext
    # Previous turns as (role, content) where role is "user" | "assistant".
    history: Tuple[Tuple[str, str], ...] = ()


class AgentRunnerPort(Protocol):
    def run(self, turn: AgentTurn) -> str: ...
