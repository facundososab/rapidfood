"""Incoming message flow and the LangChain agent adapter."""
from __future__ import annotations

from types import SimpleNamespace

import pytest
from langchain_core.messages import AIMessage

from modules.conversation.domain.models.agent_execution_context import (
    AgentExecutionContext,
)
from modules.conversation.domain.errors import NoActiveOrderError
from modules.conversation.application.ports.driven.agent_runner import AgentTurn
from modules.conversation.application.use_cases.handle_incoming_message import (
    HandleIncomingMessageCommand,
    HandleIncomingMessageUseCase,
    message_id_for,
)
from modules.conversation.domain.value_objects import MessageRole
from modules.conversation.infrastructure.adapters.driver.langchain.langchain_conversation_agent_adapter import (
    LangChainConversationAgentAdapter,
)


class FakeMessageRepository:
    def __init__(self):
        self.messages = []

    def add(self, message):
        self.messages.append(message)
        return message

    def list_by_conversation(self, conversation_id):
        return [m for m in self.messages if m.conversation_id == conversation_id]


class FakeClock:
    def now(self):
        from datetime import datetime, timezone

        return datetime(2026, 9, 17, tzinfo=timezone.utc)


class FakeRunner:
    def __init__(self, response="Listo", error=None):
        self.response = response
        self.error = error
        self.turns = []

    def run(self, turn):
        self.turns.append(turn)
        if self.error:
            raise self.error
        return self.response


def _context(**overrides):
    values = dict(
        business_configuration_id="biz-1",
        conversation_id="conv-1",
        channel="LANGSMITH",
        external_message_id="msg-1",
    )
    values.update(overrides)
    return AgentExecutionContext(**values)


def _use_case(runner, repository=None):
    repository = repository or FakeMessageRepository()
    return HandleIncomingMessageUseCase(repository, runner, FakeClock()), repository


def test_persists_user_then_assistant():
    runner = FakeRunner(response="Tenemos estas hamburguesas...")
    use_case, repository = _use_case(runner)

    result = use_case.execute(
        HandleIncomingMessageCommand(
            context=_context(external_message_id="11111111-1111-1111-1111-111111111111"),
            content="¿Qué hamburguesas tienen?",
        )
    )

    assert result.response == "Tenemos estas hamburguesas..."
    roles = [m.role for m in repository.messages]
    assert roles == ["USER", "AGENT"]
    assert repository.messages[0].message_id == "11111111-1111-1111-1111-111111111111"
    assert result.assistant_message_id == repository.messages[1].message_id


def test_user_message_is_persisted_before_the_agent_runs():
    seen = {}

    class InspectingRunner:
        def run(self, turn):
            seen["roles_at_run"] = [m.role for m in repository.messages]
            return "ok"

    repository = FakeMessageRepository()
    use_case = HandleIncomingMessageUseCase(repository, InspectingRunner(), FakeClock())

    use_case.execute(HandleIncomingMessageCommand(context=_context(), content="hola"))

    assert seen["roles_at_run"] == ["USER"]


def test_agent_failure_keeps_the_user_message():
    repository = FakeMessageRepository()
    runner = FakeRunner(error=RuntimeError("model down"))
    use_case = HandleIncomingMessageUseCase(repository, runner, FakeClock())

    with pytest.raises(RuntimeError):
        use_case.execute(HandleIncomingMessageCommand(context=_context(), content="hola"))

    assert [m.role for m in repository.messages] == ["USER"]


def test_history_is_passed_without_the_new_message():
    runner = FakeRunner()
    use_case, repository = _use_case(runner)

    use_case.execute(HandleIncomingMessageCommand(context=_context(), content="uno"))
    use_case.execute(
        HandleIncomingMessageCommand(
            context=_context(external_message_id="msg-2"), content="dos"
        )
    )

    second_turn = runner.turns[1]
    assert second_turn.message == "dos"
    assert [content for _, content in second_turn.history] == ["uno", "Listo"]
    # The history carries the STORED domain roles, not a rewritten vocabulary.
    assert [role for role, _ in second_turn.history] == [
        MessageRole.USER,
        MessageRole.AGENT,
    ]


def test_the_langchain_adapter_returns_the_final_assistant_text(monkeypatch):
    captured = {}

    class FakeAgent:
        def invoke(self, payload, config=None):
            captured["messages"] = payload["messages"]
            captured["config"] = config
            return {"messages": [*payload["messages"], AIMessage(content="Tu pedido está listo")]}

    def fake_create_agent(model, tools, system_prompt=None):
        captured["tools"] = tools
        captured["prompt"] = system_prompt
        return FakeAgent()

    monkeypatch.setattr(
        "modules.conversation.infrastructure.adapters.driver.langchain.langchain_conversation_agent_adapter.create_agent",
        fake_create_agent,
    )

    container = SimpleNamespace()
    adapter = LangChainConversationAgentAdapter(container, model=object())
    turn = AgentTurn(
        message="¿cómo viene mi pedido?",
        context=_context(),
        history=((MessageRole.USER, "hola"), (MessageRole.AGENT, "¡Hola!")),
    )

    response = adapter.run(turn)

    assert response == "Tu pedido está listo"
    assert len(captured["tools"]) == 17
    assert [m.type for m in captured["messages"]] == ["human", "ai", "human"]
    assert "NUNCA inventes" in captured["prompt"]


def test_history_from_the_real_flow_maps_agent_replies_to_ai_messages(monkeypatch):
    """Regression: the stored roles must reach the model as ai/human.

    The previous hand-written test used lowercase ("assistant") strings the use
    case never produces, so every historical message silently became a human
    message and the agent read its own replies as the customer's.
    """
    captured = {}

    class FakeAgent:
        def invoke(self, payload, config=None):
            captured["types"] = [m.type for m in payload["messages"]]
            return {"messages": [*payload["messages"], AIMessage(content="ok")]}

    monkeypatch.setattr(
        "modules.conversation.infrastructure.adapters.driver.langchain.langchain_conversation_agent_adapter.create_agent",
        lambda model, tools, system_prompt=None: FakeAgent(),
    )

    runner = FakeRunner(response="¡Hola! ¿Qué querés pedir?")
    use_case, _ = _use_case(runner)
    use_case.execute(HandleIncomingMessageCommand(context=_context(), content="hola"))
    use_case.execute(
        HandleIncomingMessageCommand(
            context=_context(external_message_id="msg-2"), content="¿cómo viene mi pedido?"
        )
    )

    adapter = LangChainConversationAgentAdapter(SimpleNamespace(), model=object())
    adapter.run(runner.turns[1])

    assert captured["types"] == ["human", "ai", "human"]


def test_an_unmappable_history_role_fails_loudly(monkeypatch):
    """A role the adapter cannot map must raise, never degrade to a human turn."""
    monkeypatch.setattr(
        "modules.conversation.infrastructure.adapters.driver.langchain.langchain_conversation_agent_adapter.create_agent",
        lambda model, tools, system_prompt=None: SimpleNamespace(
            invoke=lambda payload, config=None: {"messages": payload["messages"]}
        ),
    )
    adapter = LangChainConversationAgentAdapter(SimpleNamespace(), model=object())
    turn = AgentTurn(
        message="hola",
        context=_context(),
        history=(("assistant", "¡Hola!"),),
    )

    with pytest.raises(ValueError, match="Unknown history role"):
        adapter.run(turn)


def test_message_id_is_a_valid_and_stable_uuid_for_any_channel_id():
    import uuid

    context = _context(external_message_id="whatsapp:abc-123")

    first = message_id_for(context)
    second = message_id_for(context)

    assert first == second  # stable across retries (idempotency)
    uuid.UUID(first)  # valid UUID for the Message primary key
    assert message_id_for(_context(external_message_id="other")) != first
    assert message_id_for(_context(conversation_id="conv-2")) != first


def test_a_uuid_external_message_id_is_used_as_is():
    value = "22222222-2222-2222-2222-222222222222"
    assert message_id_for(_context(external_message_id=value)) == value


def test_a_missing_external_message_id_generates_a_random_uuid():
    import uuid

    first = message_id_for(_context(external_message_id=None))
    second = message_id_for(_context(external_message_id=None))

    uuid.UUID(first)
    assert first != second


def test_groq_model_factory_uses_the_configured_model_and_key(monkeypatch):
    import langchain_groq

    captured = {}

    class FakeGroq:
        def __init__(self, **kwargs):
            captured.update(kwargs)

    monkeypatch.setattr(langchain_groq, "ChatGroq", FakeGroq)

    from modules.conversation.infrastructure.adapters.driver.langchain.langchain_conversation_agent_adapter import (
        build_agent_model,
    )

    build_agent_model("llama-3.3-70b-versatile", "test-key")

    assert captured["model"] == "llama-3.3-70b-versatile"
    assert captured["api_key"] == "test-key"
    # No temperature is sent unless explicitly requested (models may fix sampling).
    assert "temperature" not in captured


def test_agent_runner_builds_with_the_configured_model(monkeypatch):
    import langchain_groq

    captured = {}

    class FakeGroq:
        def __init__(self, **kwargs):
            captured.update(kwargs)

    monkeypatch.setattr(langchain_groq, "ChatGroq", FakeGroq)

    from modules.conversation.infrastructure.adapters.driver.langchain.langchain_conversation_agent_adapter import (
        build_agent_runner,
    )

    runner = build_agent_runner(SimpleNamespace(), model_name="llama-3.1-8b-instant", api_key="k")

    assert captured["model"] == "llama-3.1-8b-instant"
    assert isinstance(runner, LangChainConversationAgentAdapter)


def test_gemini_model_factory_uses_the_configured_model_and_key(monkeypatch):
    import langchain_google_genai

    captured = {}

    class FakeGemini:
        def __init__(self, **kwargs):
            captured.update(kwargs)

    monkeypatch.setattr(langchain_google_genai, "ChatGoogleGenerativeAI", FakeGemini)

    from modules.conversation.infrastructure.adapters.driver.langchain.langchain_conversation_agent_adapter import (
        build_agent_model,
    )

    build_agent_model("gemini-3.5-flash-lite", "g-key", provider="gemini")

    assert captured["model"] == "gemini-3.5-flash-lite"
    assert captured["api_key"] == "g-key"


def test_agent_provider_resolution_infers_from_the_model_name():
    from composition.container import _resolve_agent_provider

    assert _resolve_agent_provider("auto", "gemini-3.5-flash-lite") == "gemini"
    assert _resolve_agent_provider("auto", "openai/gpt-oss-120b") == "groq"
    # An explicit provider always wins over the inference.
    assert _resolve_agent_provider("groq", "gemini-3.5-flash-lite") == "groq"
    assert _resolve_agent_provider("gemini", "llama-3.3-70b-versatile") == "gemini"


def test_trace_metadata_never_includes_secrets(monkeypatch):
    monkeypatch.setenv("GROQ_API_KEY", "super-secret")
    from modules.conversation.application.ports.driven.agent_runner import AgentTurn
    from modules.conversation.infrastructure.adapters.driver.langchain.langchain_conversation_agent_adapter import (
        _trace_config,
    )

    config = _trace_config(AgentTurn(message="hola", context=_context()))
    serialized = str(config)

    assert "super-secret" not in serialized
    assert config["metadata"]["channel"] == "LANGSMITH"
    assert config["metadata"]["businessConfigId"] == "biz-1"
    assert config["metadata"]["conversationId"] == "conv-1"


def test_agent_prompt_includes_the_live_order_state(monkeypatch):
    """The order is the source of truth: the model must SEE it every turn.

    This is what prevents re-adding an item that is already in the order based on
    a reconstruction from the chat history.
    """
    captured = {}

    class FakeAgent:
        def invoke(self, payload, config=None):
            return {"messages": [*payload["messages"], AIMessage(content="ok")]}

    def fake_create_agent(model, tools, system_prompt=None):
        captured["prompt"] = system_prompt
        return FakeAgent()

    monkeypatch.setattr(
        "modules.conversation.infrastructure.adapters.driver.langchain.langchain_conversation_agent_adapter.create_agent",
        fake_create_agent,
    )

    class SummaryUseCase:
        def execute(self, context):
            return SimpleNamespace(
                order_id="o-1",
                status="DRAFT",
                version=3,
                lines=[
                    SimpleNamespace(
                        product_variant_id="v-doble",
                        line_id="l-1",
                        quantity=1,
                        unit_price="9500",
                    )
                ],
                subtotal="9500",
                discount="0",
                shipping_cost=None,
                total_amount="9500",
                delivery_type=None,
                payment_type=None,
                missing_requirements=("payment_type",),
            )

    container = SimpleNamespace(get_order_summary_use_case=SummaryUseCase())
    adapter = LangChainConversationAgentAdapter(container, model=object())
    adapter.run(AgentTurn(message="sumale una coca", context=_context()))

    prompt = captured["prompt"]
    assert "ESTADO ACTUAL DEL PEDIDO" in prompt
    assert "v-doble" in prompt
    assert "line_id=l-1" in prompt
    assert "cantidad=1" in prompt


def test_agent_prompt_tolerates_a_conversation_without_order(monkeypatch):
    captured = {}

    class FakeAgent:
        def invoke(self, payload, config=None):
            return {"messages": [*payload["messages"], AIMessage(content="ok")]}

    def fake_create_agent(model, tools, system_prompt=None):
        captured["prompt"] = system_prompt
        return FakeAgent()

    monkeypatch.setattr(
        "modules.conversation.infrastructure.adapters.driver.langchain.langchain_conversation_agent_adapter.create_agent",
        fake_create_agent,
    )

    class NoOrderUseCase:
        def execute(self, context):
            raise NoActiveOrderError("no order")

    container = SimpleNamespace(get_order_summary_use_case=NoOrderUseCase())
    adapter = LangChainConversationAgentAdapter(container, model=object())
    adapter.run(AgentTurn(message="hola", context=_context()))

    assert "todavía no tiene un pedido" in captured["prompt"]


def test_system_prompt_translates_mercado_pago_to_online():
    from modules.conversation.infrastructure.adapters.driver.langchain.prompt import (
        SYSTEM_PROMPT,
    )

    assert "Mercado Pago" in SYSTEM_PROMPT
    assert "SIEMPRE lo traducís a ONLINE" in SYSTEM_PROMPT
