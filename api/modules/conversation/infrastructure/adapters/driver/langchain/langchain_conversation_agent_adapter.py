"""LangChain/LangGraph driver adapter implementing `AgentRunnerPort`.

It interprets the message, lets the model select tools, runs them (each tool
delegates to a conversation use case with the trusted context) and returns the
final assistant text. Framework types stay inside this adapter.
"""
from __future__ import annotations

import os
from typing import Any, Iterable, Optional

from langchain.agents import create_agent
from langchain_core.messages import AIMessage, BaseMessage, HumanMessage

from modules.conversation.application.ports.driven.agent_runner import (
    AgentRunnerPort,
    AgentTurn,
)
from modules.conversation.infrastructure.adapters.driver.langchain.prompt import (
    SYSTEM_PROMPT,
)
from modules.conversation.infrastructure.adapters.driver.langchain.tools import (
    build_tools,
)


class LangChainConversationAgentAdapter(AgentRunnerPort):
    def __init__(self, container: Any, model: Any, prompt: str = SYSTEM_PROMPT) -> None:
        self._container = container
        self._model = model
        self._prompt = prompt

    def run(self, turn: AgentTurn) -> str:
        tools = build_tools(self._container, turn.context)
        agent = create_agent(self._model, tools, system_prompt=self._prompt)

        messages: list[BaseMessage] = [
            _to_message(role, content) for role, content in turn.history
        ]
        messages.append(HumanMessage(content=turn.message))

        result = agent.invoke({"messages": messages}, _trace_config(turn))
        return _final_text(result["messages"])


def _trace_config(turn: AgentTurn) -> dict:
    """LangSmith metadata for one turn: useful, and never a secret.

    No API keys, tokens, credentials or DB URLs are attached.
    """
    context = turn.context
    is_dev = os.environ.get("DJANGO_DEBUG", "0") == "1"
    metadata = {
        "environment": "dev" if is_dev else "prod",
        "channel": context.channel,
        "businessConfigId": context.business_configuration_id,
        "conversationId": context.conversation_id,
        "externalThreadId": context.external_thread_id,
    }
    if context.client_id:
        metadata["clientId"] = context.client_id
    return {"metadata": {k: v for k, v in metadata.items() if v is not None}}


def _to_message(role: str, content: str) -> BaseMessage:
    if role == "assistant":
        return AIMessage(content=content)
    return HumanMessage(content=content)


def _final_text(messages: Iterable[BaseMessage]) -> str:
    for message in reversed(list(messages)):
        if isinstance(message, AIMessage):
            text = _content_text(message.content)
            if text:
                return text
    return ""


def _content_text(content: Any) -> str:
    if isinstance(content, str):
        return content
    if isinstance(content, list):
        parts = []
        for block in content:
            if isinstance(block, str):
                parts.append(block)
            elif isinstance(block, dict) and block.get("type") == "text":
                parts.append(str(block.get("text", "")))
        return "".join(parts).strip()
    return str(content) if content else ""


def build_agent_model(model_name: str, api_key: str, temperature: Optional[float] = None):
    """Groq chat model factory.

    Kept here so the application never imports a model provider; swapping
    providers only touches this function. ``temperature`` is only sent when the
    caller sets one.
    """
    from langchain_groq import ChatGroq

    kwargs: dict[str, Any] = {"model": model_name, "api_key": api_key}
    if temperature is not None:
        kwargs["temperature"] = temperature
    return ChatGroq(**kwargs)


def build_agent_runner(
    container: Any, model_name: str, api_key: str, prompt: Optional[str] = None
) -> LangChainConversationAgentAdapter:
    model = build_agent_model(model_name, api_key)
    return LangChainConversationAgentAdapter(
        container, model, prompt or SYSTEM_PROMPT
    )
