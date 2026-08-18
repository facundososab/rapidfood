from __future__ import annotations

from rest_framework.response import Response
from rest_framework.views import APIView

from modules.conversation.application.ports.driver.conversation_commands import (
    ListMessagesQuery,
    ReceiveMessageCommand,
)
from modules.conversation.infrastructure.adapters.driver.rest.serializers import WebhookSerializer


class ConversationWebhookView(APIView):
    container = None

    def post(self, request):
        if self.container is None:
            raise RuntimeError("ConversationWebhookView.container is not configured")
        serializer = WebhookSerializer(data=request.data)
        serializer.is_valid(raise_exception=True)
        result = self.container.receive_message_use_case.execute(
            ReceiveMessageCommand(
                channel=serializer.validated_data["channel"],
                channel_identity=serializer.validated_data["channel_identity"],
                content=serializer.validated_data["content"],
                external_message_id=serializer.validated_data.get("external_message_id"),
            )
        )
        return Response(
            {
                "conversation_id": result.conversation_id,
                "user_message_id": result.user_message_id,
                "agent_message_id": result.agent_message_id,
                "intent": result.intent,
                "response": result.response,
            }
        )


class ConversationMessagesView(APIView):
    container = ConversationWebhookView.container

    def get(self, request, conversation_id: str):
        if self.container is None:
            raise RuntimeError("ConversationMessagesView.container is not configured")
        result = self.container.list_messages_use_case.execute(ListMessagesQuery(conversation_id=conversation_id))
        return Response(
            {
                "conversation_id": result.conversation_id,
                "messages": [
                    {
                        "message_id": message.message_id,
                        "conversation_id": message.conversation_id,
                        "role": message.role,
                        "content": message.content,
                        "detected_intent": message.detected_intent,
                        "sentiment": message.sentiment,
                        "status": message.status,
                        "created_at": message.created_at,
                    }
                    for message in result.messages
                ],
            }
        )
