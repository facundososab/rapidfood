def test_webhook_serializer_rejects_missing_payload_fields():
    from api.modules.conversation.infrastructure.adapters.driver.rest.serializers import WebhookSerializer

    serializer = WebhookSerializer(data={"channel": "WHATSAPP"})
    assert serializer.is_valid() is False
    assert "channel_identity" in serializer.errors
    assert "content" in serializer.errors


def test_webhook_view_route_is_resolvable():
    from django.urls import resolve

    match = resolve("/conversation/webhook/")
    assert match.url_name == "conversation-webhook"


def test_webhook_endpoint_persists_and_returns_transport_safe_payload():
    from django.test import Client
    from api.modules.conversation.configuration.container import build_container
    from api.modules.conversation.infrastructure.adapters.driver.rest.views import (
        ConversationMessagesView,
        ConversationWebhookView,
    )

    ConversationWebhookView.container = build_container()
    ConversationMessagesView.container = ConversationWebhookView.container

    client = Client()
    response = client.post(
        "/conversation/webhook/",
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


def test_messages_endpoint_returns_chronological_history():
    from django.test import Client
    from api.modules.conversation.configuration.container import build_container
    from api.modules.conversation.infrastructure.adapters.driver.rest.views import (
        ConversationMessagesView,
        ConversationWebhookView,
    )

    ConversationWebhookView.container = build_container()
    ConversationMessagesView.container = ConversationWebhookView.container

    client = Client()
    first = client.post(
        "/conversation/webhook/",
        data={"channel": "WHATSAPP", "channel_identity": "+5491112345678", "content": "Quiero pedir una pizza"},
        content_type="application/json",
    ).json()

    response = client.get(f"/conversation/{first['conversation_id']}/messages/")
    assert response.status_code == 200
    payload = response.json()
    assert payload["conversation_id"] == first["conversation_id"]
    assert [message["role"] for message in payload["messages"]] == ["USER", "AGENT"]
