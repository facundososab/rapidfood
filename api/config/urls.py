"""URL routing — Rapidfood."""

from django.urls import include, path

from api.config import views
from api.modules.conversation.configuration.container import build_container
from api.modules.conversation.infrastructure.adapters.driver.rest.views import (
    ConversationMessagesView,
    ConversationWebhookView,
)

_conversation_container = build_container()
ConversationWebhookView.container = _conversation_container
ConversationMessagesView.container = _conversation_container

urlpatterns = [
    path("health/", views.health, name="health"),
    path("conversation/", include("api.modules.conversation.infrastructure.adapters.driver.rest.urls")),
]
