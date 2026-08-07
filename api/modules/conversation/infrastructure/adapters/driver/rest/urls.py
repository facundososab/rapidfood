from django.urls import path

from api.modules.conversation.infrastructure.adapters.driver.rest.views import (
    ConversationMessagesView,
    ConversationWebhookView,
)

urlpatterns = [
    path("webhook/", ConversationWebhookView.as_view(), name="conversation-webhook"),
    path("<str:conversation_id>/messages/", ConversationMessagesView.as_view(), name="conversation-messages"),
]
