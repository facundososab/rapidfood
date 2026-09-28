import pytest

from modules.conversation.configuration.container import build_container
from modules.conversation.tests.fakes import (
    InMemoryConversationRepository,
    InMemoryMessageRepository,
)


@pytest.fixture
def container(monkeypatch):
    """Wires the REST views to an in-memory conversation container."""
    built = build_container(
        conversation_repository=InMemoryConversationRepository(),
        message_repository=InMemoryMessageRepository(),
    )
    monkeypatch.setattr(
        "modules.conversation.infrastructure.adapters.driver.rest.views.get_app_conversation_container",
        lambda: built,
    )
    return built


def test_webhook_serializer_rejects_missing_payload_fields():
    from modules.conversation.infrastructure.adapters.driver.rest.serializers import WebhookSerializer

    serializer = WebhookSerializer(data={"channel": "WHATSAPP"})
    assert serializer.is_valid() is False
    assert "channel_identity" in serializer.errors
    assert "content" in serializer.errors


def test_webhook_view_route_is_resolvable():
    from django.urls import resolve

    match = resolve("/api/conversation/webhook/")
    assert match.url_name == "conversation-webhook"


def test_webhook_endpoint_persists_and_returns_transport_safe_payload(container):
    from django.test import Client

    client = Client()
    response = client.post(
        "/api/conversation/webhook/",
        data={"channel": "WHATSAPP", "channel_identity": "+5491112345678", "content": "Quiero pedir una pizza"},
        content_type="application/json",
    )

    assert response.status_code == 200
    payload = response.json()
    assert set(payload) == {"conversation_id", "user_message_id", "agent_message_id", "intent", "response"}
    assert payload["conversation_id"]
    assert payload["user_message_id"]
    assert payload["agent_message_id"]
    assert payload["intent"] == "START_ORDER"


def test_messages_endpoint_returns_chronological_history(container):
    from django.test import Client

    client = Client()
    first = client.post(
        "/api/conversation/webhook/",
        data={"channel": "WHATSAPP", "channel_identity": "+5491112345678", "content": "Quiero pedir una pizza"},
        content_type="application/json",
    ).json()

    response = client.get(f"/api/conversation/{first['conversation_id']}/messages/")
    assert response.status_code == 200
    payload = response.json()
    assert payload["conversation_id"] == first["conversation_id"]
    assert [message["role"] for message in payload["messages"]] == ["USER", "AGENT"]


class _StubUseCase:
    def __init__(self, result):
        self.result = result
        self.commands = []

    def execute(self, command):
        self.commands.append(command)
        return self.result


def test_agent_endpoint_resolves_identity_from_the_driver(monkeypatch):
    from types import SimpleNamespace
    from django.test import Client

    monkeypatch.setattr(
        "composition.container.resolve_agent_business_config_id",
        lambda requested=None: requested or "biz-1",
    )


    from modules.conversation.application.use_cases.resolve_conversation_for_channel import (
        ResolveConversationResult,
    )
    from modules.conversation.application.use_cases.handle_incoming_message import (
        HandleIncomingMessageResult,
    )

    resolve = _StubUseCase(ResolveConversationResult(conversation_id="conv-1", client_id=None, created=True))
    handle = _StubUseCase(
        HandleIncomingMessageResult(
            conversation_id="conv-1",
            user_message_id="u-1",
            assistant_message_id="a-1",
            response="Hola, ¿qué querés pedir?",
        )
    )
    stub_container = SimpleNamespace(
        resolve_conversation_use_case=resolve,
        handle_incoming_message_use_case=handle,
    )
    monkeypatch.setattr(
        "modules.conversation.infrastructure.adapters.driver.rest.views.get_app_conversation_container",
        lambda: stub_container,
    )

    response = Client().post(
        "/api/conversation/agent/message/",
        data={
            "business_config_id": "biz-1",
            "channel": "LANGSMITH",
            "external_thread_id": "thread-1",
            "external_message_id": "msg-1",
            "content": "hola",
        },
        content_type="application/json",
    )

    assert response.status_code == 200
    assert response.json()["response"] == "Hola, ¿qué querés pedir?"
    assert resolve.commands[0].external_thread_id == "thread-1"
    context = handle.commands[0].context
    assert context.business_configuration_id == "biz-1"
    assert context.conversation_id == "conv-1"
    assert context.external_message_id == "msg-1"


def test_agent_endpoint_is_unavailable_without_an_agent_runner(monkeypatch):
    from types import SimpleNamespace
    from django.test import Client

    monkeypatch.setattr(
        "composition.container.resolve_agent_business_config_id",
        lambda requested=None: requested or "biz-1",
    )


    monkeypatch.setattr(
        "modules.conversation.infrastructure.adapters.driver.rest.views.get_app_conversation_container",
        lambda: SimpleNamespace(handle_incoming_message_use_case=None),
    )

    response = Client().post(
        "/api/conversation/agent/message/",
        data={
            "business_config_id": "biz-1",
            "external_thread_id": "thread-1",
            "content": "hola",
        },
        content_type="application/json",
    )

    assert response.status_code == 503


def test_agent_endpoint_returns_a_clean_error_when_the_agent_fails(monkeypatch):
    from types import SimpleNamespace
    from django.test import Client

    monkeypatch.setattr(
        "composition.container.resolve_agent_business_config_id",
        lambda requested=None: requested or "biz-1",
    )


    class FailingUseCase:
        def execute(self, command):
            raise RuntimeError("quota exceeded: internal detail")

    stub_container = SimpleNamespace(
        resolve_conversation_use_case=SimpleNamespace(
            execute=lambda command: SimpleNamespace(
                conversation_id="conv-1", client_id=None, created=False
            )
        ),
        handle_incoming_message_use_case=FailingUseCase(),
    )
    monkeypatch.setattr(
        "modules.conversation.infrastructure.adapters.driver.rest.views.get_app_conversation_container",
        lambda: stub_container,
    )

    response = Client().post(
        "/api/conversation/agent/message/",
        data={
            "business_config_id": "biz-1",
            "external_thread_id": "thread-1",
            "content": "hola",
        },
        content_type="application/json",
    )

    assert response.status_code == 502
    body = response.content.decode()
    assert "quota" not in body
    assert "Traceback" not in body
