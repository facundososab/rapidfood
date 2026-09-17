from django.urls import path

from modules.conversation.infrastructure.adapters.driver.rest.views import (
    AgentMessageView,
    ConversationMessagesView,
    ConversationWebhookView,
)

urlpatterns = [
    path("webhook/", ConversationWebhookView.as_view(), name="conversation-webhook"),
    path("agent/message/", AgentMessageView.as_view(), name="conversation-agent-message"),
    path("<str:conversation_id>/messages/", ConversationMessagesView.as_view(), name="conversation-messages"),
]
