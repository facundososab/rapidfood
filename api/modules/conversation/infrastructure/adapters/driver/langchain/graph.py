"""LangGraph Agent Server / Studio entrypoint for the Rapidfood agent.

This is the channel DRIVER for LangSmith (the same role WhatsApp will have
later): it only resolves the trusted execution context from the thread and
delegates to the REAL conversation flow — `HandleIncomingMessageUseCase` — which
persists the USER message, runs the LangChain agent with the context-bound tools,
and persists the ASSISTANT message. No business logic lives here.

    Studio message
      -> resolve Conversation (thread_id -> Conversation.externalThreadId)
      -> persist USER message
      -> LangChainConversationAgentAdapter -> tools -> conversation use cases
      -> persist ASSISTANT message
      -> response

Identity rules: `thread_id` is the EXTERNAL conversation identity; the business
and client come from the graph runtime context (with a documented DEV fallback),
never from the model and never typed by the user in the chat.
"""
from __future__ import annotations

import os
import sys
import uuid
from pathlib import Path

# `langgraph dev` imports this module by file path; make the `api` root
# importable so `modules.*` / `composition.*` resolve without setting PYTHONPATH.
_API_ROOT = Path(__file__).resolve().parents[6]
if str(_API_ROOT) not in sys.path:
    sys.path.insert(0, str(_API_ROOT))

from typing import Any, Optional  # noqa: E402

from langchain_core.messages import AIMessage, BaseMessage  # noqa: E402
from langchain_core.runnables import RunnableConfig  # noqa: E402
from langgraph.graph import END, START, MessagesState, StateGraph  # noqa: E402

CHANNEL = "LANGSMITH"


_DJANGO_READY = False


def _ensure_django() -> None:
    """Configure Django settings exactly once (also loads .env into os.environ).

    Must run BEFORE any container is built: the delivery container reads Django
    settings at construction time. Idempotent, and tolerant of a host process
    that already populated Django (e.g. tests).
    """
    global _DJANGO_READY
    if _DJANGO_READY:
        return
    os.environ.setdefault("DJANGO_SETTINGS_MODULE", "config.settings")
    import django

    try:
        django.setup()
    except RuntimeError:
        # Already configured/populated by the host process.
        pass
    _DJANGO_READY = True


def _runtime(config: Optional[dict]) -> dict:
    return (config or {}).get("configurable") or {}


def resolve_business_and_client(config: Optional[dict]) -> tuple[str, Optional[str]]:
    """businessConfigId / clientId from the graph runtime context.

    Preferred (multi-tenant correct): the caller passes them as runtime context,
    e.g. `configurable = {"business_config_id": ..., "client_id": ...}`.

    DEV FALLBACK: with no runtime context it falls back to
    `AGENT_BUSINESS_CONFIG_ID` and, if that is missing or stale, to the single
    existing business (see `resolve_agent_business_config_id`). That keeps the
    first manual tests working across database re-seeds. It is NOT the definitive
    multi-tenant design.
    """
    _ensure_django()
    from composition.container import resolve_agent_business_config_id

    configurable = _runtime(config)
    requested = configurable.get("business_config_id") or configurable.get(
        "businessConfigId"
    )
    business_id = resolve_agent_business_config_id(requested)
    client_id = configurable.get("client_id") or configurable.get("clientId")
    return business_id, client_id


def last_user_text(messages: list[BaseMessage]) -> str:
    for message in reversed(list(messages)):
        if getattr(message, "type", None) == "human":
            content = message.content
            if isinstance(content, str):
                return content
            if isinstance(content, list):
                return "".join(
                    block.get("text", "") if isinstance(block, dict) else str(block)
                    for block in content
                ).strip()
    return ""


def run_turn(state: MessagesState, config: Optional[RunnableConfig] = None) -> str:
    """Run ONE real agent turn and return the assistant response.

    Reuses the same use cases and adapters as the HTTP driver; nothing is
    reimplemented here.
    """
    from composition.container import get_app_conversation_container
    from modules.conversation.domain.models.agent_execution_context import (
        AgentExecutionContext,
    )
    from modules.conversation.application.use_cases.handle_incoming_message import (
        HandleIncomingMessageCommand,
    )
    from modules.conversation.application.use_cases.resolve_conversation_for_channel import (
        ResolveConversationCommand,
    )

    _ensure_django()
    container = get_app_conversation_container()
    if container.handle_incoming_message_use_case is None:
        raise RuntimeError(
            "The agent is not configured (missing GROQ_API_KEY)."
        )

    configurable = _runtime(config)
    thread_id = configurable.get("thread_id") or "default"
    business_id, client_id = resolve_business_and_client(config)

    # thread_id identifies a CONVERSATION (never an Order); it is stored as the
    # external thread id, not as the internal conversation id.
    resolution = container.resolve_conversation_use_case.execute(
        ResolveConversationCommand(
            business_config_id=business_id,
            channel=CHANNEL,
            external_thread_id=thread_id,
            client_id=client_id,
        )
    )

    context = AgentExecutionContext(
        business_configuration_id=business_id,
        conversation_id=resolution.conversation_id,
        channel=CHANNEL,
        client_id=resolution.client_id,
        external_thread_id=thread_id,
        # Generated ONCE per ingress and propagated to every tool of this turn.
        # It is NOT the tracing run_id (which changes on every retry).
        external_message_id=str(uuid.uuid4()),
    )

    result = container.handle_incoming_message_use_case.execute(
        HandleIncomingMessageCommand(
            context=context, content=last_user_text(state["messages"])
        )
    )
    return result.response


def _agent_node(state: MessagesState, config: RunnableConfig) -> dict:
    response = run_turn(state, config)
    return {"messages": [AIMessage(content=response)]}


def build_graph():
    graph = StateGraph(MessagesState)
    graph.add_node("agent", _agent_node)
    graph.add_edge(START, "agent")
    graph.add_edge("agent", END)
    return graph.compile()


# LangGraph Agent Server / Studio looks for this object.
graph = build_graph()
