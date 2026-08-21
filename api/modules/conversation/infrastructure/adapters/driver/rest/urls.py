from django.urls import path

from modules.conversation.configuration.container import build_container
from modules.conversation.infrastructure.adapters.driver.rest.views import (
    ConversationMessagesView,
    ConversationWebhookView,
)

_container = build_container()
ConversationWebhookView.container = _container
ConversationMessagesView.container = _container

urlpatterns = [
    path("webhook/", ConversationWebhookView.as_view(), name="conversation-webhook"),
    path("<str:conversation_id>/messages/", ConversationMessagesView.as_view(), name="conversation-messages"),
]
