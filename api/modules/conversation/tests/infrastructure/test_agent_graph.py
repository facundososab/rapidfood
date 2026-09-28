"""The LangGraph Agent Server / Studio entrypoint (no LLM, no DB)."""
from types import SimpleNamespace

import pytest
from langchain_core.messages import AIMessage, HumanMessage

from modules.conversation.infrastructure.adapters.driver.langchain.graph import (
    CHANNEL,
    build_graph,
    last_user_text,
    resolve_business_and_client,
    run_turn,
)


def test_graph_compiles():
    graph = build_graph()
    assert graph is not None
    assert set(graph.get_graph().nodes) == {"__start__", "agent", "__end__"}


def test_channel_is_the_test_driver_not_whatsapp():
    assert CHANNEL == "LANGSMITH"


def test_runtime_context_is_passed_to_the_resolver(monkeypatch):
    calls = []

    def fake_resolver(requested=None):
        calls.append(requested)
        return "resolved-biz"

    monkeypatch.setattr(
        "composition.container.resolve_agent_business_config_id", fake_resolver
    )
    config = {"configurable": {"business_config_id": "runtime-biz", "client_id": "c-1"}}

    assert resolve_business_and_client(config) == ("resolved-biz", "c-1")
    assert calls == ["runtime-biz"]


def test_no_runtime_context_lets_the_resolver_fall_back(monkeypatch):
    calls = []

    def fake_resolver(requested=None):
        calls.append(requested)
        return "single-biz"

    monkeypatch.setattr(
        "composition.container.resolve_agent_business_config_id", fake_resolver
    )

    assert resolve_business_and_client({"configurable": {"thread_id": "t-1"}}) == (
        "single-biz",
        None,
    )
    assert calls == [None]


def test_unresolvable_business_raises(monkeypatch):
    def failing_resolver(requested=None):
        raise RuntimeError("No business configuration found.")

    monkeypatch.setattr(
        "composition.container.resolve_agent_business_config_id", failing_resolver
    )
    with pytest.raises(RuntimeError):
        resolve_business_and_client({"configurable": {"thread_id": "t-1"}})


def test_last_user_text_reads_the_human_message():
    messages = [
        HumanMessage(content="¿Qué hamburguesas tienen?"),
        AIMessage(content="Tenemos..."),
        HumanMessage(content="Quiero una doble"),
    ]
    assert last_user_text(messages) == "Quiero una doble"


class _StubUseCase:
    def __init__(self, result):
        self.result = result
        self.commands = []

    def execute(self, command):
        self.commands.append(command)
        return self.result


def test_run_turn_uses_the_real_flow_and_persists_through_it(monkeypatch):
    from modules.conversation.application.use_cases.handle_incoming_message import (
        HandleIncomingMessageResult,
    )
    from modules.conversation.application.use_cases.resolve_conversation_for_channel import (
        ResolveConversationResult,
    )

    resolve = _StubUseCase(
        ResolveConversationResult(conversation_id="conv-1", client_id=None, created=True)
    )
    handle = _StubUseCase(
        HandleIncomingMessageResult(
            conversation_id="conv-1",
            user_message_id="u-1",
            assistant_message_id="a-1",
            response="Tenemos estas hamburguesas...",
        )
    )
    stub_container = SimpleNamespace(
        resolve_conversation_use_case=resolve,
        handle_incoming_message_use_case=handle,
    )
    monkeypatch.setattr(
        "composition.container.get_app_conversation_container", lambda: stub_container
    )
    monkeypatch.setattr(
        "composition.container.resolve_agent_business_config_id",
        lambda requested=None: "biz-1",
    )

    config = {"configurable": {"thread_id": "thread-1"}}
    state = {"messages": [HumanMessage(content="¿Qué hamburguesas tienen?")]}

    response = run_turn(state, config)

    assert response == "Tenemos estas hamburguesas..."
    # The driver resolves the conversation from the thread (external identity).
    assert resolve.commands[0].business_config_id == "biz-1"
    assert resolve.commands[0].channel == "LANGSMITH"
    assert resolve.commands[0].external_thread_id == "thread-1"
    # The real flow receives the trusted context and the message text.
    command = handle.commands[0]
    assert command.content == "¿Qué hamburguesas tienen?"
    assert command.context.conversation_id == "conv-1"
    assert command.context.external_thread_id == "thread-1"
    assert command.context.business_configuration_id == "biz-1"
    # externalMessageId is generated once per ingress, never reused as an order id.
    assert command.context.external_message_id
    assert command.context.external_message_id != "thread-1"


def test_run_turn_without_an_agent_runner_raises(monkeypatch):
    monkeypatch.setattr(
        "composition.container.get_app_conversation_container",
        lambda: SimpleNamespace(handle_incoming_message_use_case=None),
    )
    with pytest.raises(RuntimeError):
        run_turn(
            {"messages": [HumanMessage(content="hola")]},
            {"configurable": {"thread_id": "t-1"}},
        )
