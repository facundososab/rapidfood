from __future__ import annotations

import logging

from rest_framework.response import Response
from rest_framework.views import APIView

from composition.container import get_app_conversation_container
from modules.conversation.domain.models.agent_execution_context import (
    AgentExecutionContext,
)
from modules.conversation.application.ports.driver.conversation_commands import (
    ListMessagesQuery,
    ReceiveMessageCommand,
)
from modules.conversation.application.use_cases.handle_incoming_message import (
    HandleIncomingMessageCommand,
)
from modules.conversation.application.use_cases.resolve_conversation_for_channel import (
    ResolveConversationCommand,
)
from modules.conversation.infrastructure.adapters.driver.rest.serializers import (
    AgentMessageSerializer,
    WebhookSerializer,
)


logger = logging.getLogger(__name__)


class ConversationWebhookView(APIView):
    """Legacy deterministic webhook.

    The agent-backed message flow (LangChain) is added separately; this endpoint
    keeps working with the same persistence so nothing regresses meanwhile.
    """

    def post(self, request):
        container = get_app_conversation_container()
        serializer = WebhookSerializer(data=request.data)
        serializer.is_valid(raise_exception=True)
        result = container.receive_message_use_case.execute(
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
    def get(self, request, conversation_id: str):
        container = get_app_conversation_container()
        result = container.list_messages_use_case.execute(
            ListMessagesQuery(conversation_id=conversation_id)
        )
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


class AgentMessageView(APIView):
    """Agent entrypoint for channel drivers (Studio/HTTP now, WhatsApp later).

    The driver resolves identity: conversation from the thread, business from the
    request/config. The model never supplies them.
    """

    def post(self, request):
        serializer = AgentMessageSerializer(data=request.data)
        serializer.is_valid(raise_exception=True)
        data = serializer.validated_data

        from composition.container import resolve_agent_business_config_id

        business_id = resolve_agent_business_config_id(data.get("business_config_id"))

        container = get_app_conversation_container()
        if container.handle_incoming_message_use_case is None:
            return Response(
                {"error": "The agent is not configured (missing GROQ_API_KEY)."},
                status=503,
            )

        resolution = container.resolve_conversation_use_case.execute(
            ResolveConversationCommand(
                business_config_id=business_id,
                channel=data["channel"],
                external_thread_id=data["external_thread_id"],
                client_id=str(data["client_id"]) if data.get("client_id") else None,
            )
        )
        context = AgentExecutionContext(
            business_configuration_id=business_id,
            conversation_id=resolution.conversation_id,
            channel=data["channel"],
            client_id=resolution.client_id,
            external_thread_id=data["external_thread_id"],
            external_message_id=data.get("external_message_id") or None,
        )

        try:
            result = container.handle_incoming_message_use_case.execute(
                HandleIncomingMessageCommand(context=context, content=data["content"])
            )
        except Exception:
            # Technical failure (model/provider/transport). The USER message is
            # already persisted; never leak a stack trace or an internal message,
            # but DO log it so it is diagnosable.
            logger.exception(
                "Agent turn failed (conversation=%s, thread=%s)",
                context.conversation_id,
                context.external_thread_id,
            )
            return Response(
                {"error": "No pude procesar el mensaje en este momento. Reintentá."},
                status=502,
            )
        return Response(
            {
                "conversation_id": result.conversation_id,
                "user_message_id": result.user_message_id,
                "assistant_message_id": result.assistant_message_id,
                "response": result.response,
            }
        )
