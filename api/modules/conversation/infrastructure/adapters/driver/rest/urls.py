from django.urls import path

from modules.conversation.infrastructure.adapters.driver.whatsapp.views import (
    WhatsAppConfigurationView,
    WhatsAppWebhookView,
)
from modules.conversation.infrastructure.adapters.driver.rest.views import (
    AgentMessageView,
    ConversationClientMessageView,
    ConversationListView,
    ConversationMessagesView,
    ConversationOperatorMessageView,
    ConversationReleaseView,
    ConversationTakeoverView,
    ConversationWebhookView,
)

urlpatterns = [
    path("", ConversationListView.as_view(), name="conversation-list"),
    path("webhook/", ConversationWebhookView.as_view(), name="conversation-webhook"),
    path(
        "webhook/whatsapp/",
        WhatsAppWebhookView.as_view(),
        name="conversation-whatsapp-webhook",
    ),
    path(
        "whatsapp/config/",
        WhatsAppConfigurationView.as_view(),
        name="conversation-whatsapp-config",
    ),
    path("agent/message/", AgentMessageView.as_view(), name="conversation-agent-message"),
    path("<str:conversation_id>/messages/", ConversationMessagesView.as_view(), name="conversation-messages"),
    path(
        "<str:conversation_id>/operator-message/",
        ConversationOperatorMessageView.as_view(),
        name="conversation-operator-message",
    ),
    path(
        "<str:conversation_id>/client-message/",
        ConversationClientMessageView.as_view(),
        name="conversation-client-message",
    ),
    path(
        "<str:conversation_id>/takeover/",
        ConversationTakeoverView.as_view(),
        name="conversation-takeover",
    ),
    path(
        "<str:conversation_id>/release/",
        ConversationReleaseView.as_view(),
        name="conversation-release",
    ),
]
