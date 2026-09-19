"""LangChain/LangGraph driver adapter implementing `AgentRunnerPort`.

It interprets the message, lets the model select tools, runs them (each tool
delegates to a conversation use case with the trusted context) and returns the
final assistant text. Framework types stay inside this adapter.
"""
from __future__ import annotations

import os
from typing import Any, Iterable, Optional

from langchain.agents import create_agent
from langchain_core.messages import AIMessage, BaseMessage, HumanMessage, SystemMessage

from modules.conversation.application.ports.driven.agent_runner import (
    AgentRunnerPort,
    AgentTurn,
)
from modules.conversation.domain.errors import NoActiveOrderError
from modules.conversation.domain.value_objects import MessageRole
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
        agent = create_agent(
            self._model,
            tools,
            system_prompt=_compose_prompt(self._prompt, self._container, turn.context),
        )

        messages: list[BaseMessage] = [
            _to_message(role, content) for role, content in turn.history
        ]
        messages.append(HumanMessage(content=turn.message))

        result = agent.invoke({"messages": messages}, _trace_config(turn))
        return _final_text(result["messages"])


def _compose_prompt(base_prompt: str, container: Any, context) -> str:
    """Base policy prompt + the LIVE order state for THIS conversation.

    The order (not the chat history) is the source of truth. Showing it on every
    turn is what stops the model from reconstructing the order out of previous
    messages and re-adding items that are already there.
    """
    return f"{base_prompt}\n\n{_order_state_block(container, context)}"


def _order_state_block(container: Any, context) -> str:
    header = (
        "ESTADO ACTUAL DEL PEDIDO (fuente de verdad, generado por el backend en "
        "este turno; NO lo reconstruyas a partir del historial)"
    )
    summary_use_case = getattr(container, "get_order_summary_use_case", None)
    if summary_use_case is None:
        return f"{header}\nNo disponible."
    try:
        summary = summary_use_case.execute(context)
    except NoActiveOrderError:
        return f"{header}\nLa conversación todavía no tiene un pedido."
    except Exception:
        # Never let a read failure break the turn; the agent falls back to tools.
        return f"{header}\nNo se pudo leer el pedido; usá get_current_order."
    return f"{header}\n{_format_order_summary(summary)}"


def _format_order_summary(summary) -> str:
    if summary.lines:
        lines = "\n".join(
            f"- variant_id={line.product_variant_id} line_id={line.line_id} "
            f"cantidad={line.quantity} precio_unitario={line.unit_price}"
            for line in summary.lines
        )
    else:
        lines = "- (sin productos todavía)"
    return (
        f"order_id={summary.order_id} estado={summary.status} versión={summary.version}\n"
        f"líneas:\n{lines}\n"
        f"subtotal={summary.subtotal} descuento={summary.discount} "
        f"envío={summary.shipping_cost} total={summary.total_amount}\n"
        f"tipo_entrega={summary.delivery_type} forma_pago={summary.payment_type}\n"
        f"faltantes={list(summary.missing_requirements)}"
    )


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


_ROLE_MESSAGES = {
    MessageRole.USER: HumanMessage,
    MessageRole.AGENT: AIMessage,
    MessageRole.SYSTEM: SystemMessage,
}


def _to_message(role: MessageRole, content: str) -> BaseMessage:
    """Map a stored DOMAIN role to its LangChain message.

    The history is persisted with `MessageRole` values ("USER" / "AGENT" /
    "SYSTEM"), so this maps on the enum - not on the framework's lowercase
    vocabulary. An unmappable role raises instead of degrading to a human
    message: degrading would make the agent read its own replies (and any human
    operator's) as if the customer had said them.
    """
    try:
        domain_role = MessageRole(str(role))
    except ValueError as exc:
        raise ValueError(f"Unknown history role: {role!r}") from exc
    return _ROLE_MESSAGES[domain_role](content=content)


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
