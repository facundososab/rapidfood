from __future__ import annotations

import logging
import uuid

from rest_framework.permissions import AllowAny
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
from modules.conversation.domain.errors import ConversationNotFoundError
from modules.conversation.infrastructure.adapters.driver.rest.serializers import (
    AgentMessageSerializer,
    SendMessageSerializer,
    WebhookSerializer,
)


logger = logging.getLogger(__name__)


class ConversationWebhookView(APIView):
    """Legacy deterministic webhook.

    The agent-backed message flow (LangChain) is added separately; this endpoint
    keeps working with the same persistence so nothing regresses meanwhile.
    """

    # Public: the WhatsApp/AI agent bridge (customer-facing) calls this
    # endpoint without staff JWTs.
    permission_classes = [AllowAny]

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
    # Public: read-side of the customer-facing conversation bridge.
    permission_classes = [AllowAny]

    def get(self, request, conversation_id: str):
        container = get_app_conversation_container()
        try:
            detail = container.get_conversation_detail_use_case.execute(conversation_id)
        except ConversationNotFoundError:
            return Response({"error": "Conversation not found"}, status=404)
        return Response(_detail_payload(detail))


def _detail_payload(detail) -> dict:
    return {
        "conversation_id": detail.conversation_id,
        "channel": detail.channel,
        "external_thread_id": detail.external_thread_id,
        "client_id": detail.client_id,
        "agent_paused": detail.agent_paused,
        "client_name": detail.client_name,
        "client_phone": detail.client_phone,
        "last_intent": detail.last_intent,
        "overall_sentiment": detail.overall_sentiment,
        "messages": [
            {
                "message_id": message.message_id,
                "role": message.role,
                "author": message.author,
                "content": message.content,
                "created_at": message.created_at,
            }
            for message in detail.messages
        ],
    }


class ConversationListView(APIView):
    """Panel: conversations with their last message and takeover state."""

    def get(self, request):
        container = get_app_conversation_container()
        return Response(
            [
                {
                    "id": c.conversation_id,
                    "channel": c.channel,
                    "external_thread_id": c.external_thread_id,
                    "client_id": c.client_id,
                    "agent_paused": c.agent_paused,
                    "message_count": c.message_count,
                    "client_name": c.client_name,
                    "client_phone": c.client_phone,
                    "last_message": c.last_message,
                    "last_role": c.last_role,
                    "last_at": c.last_at,
                }
                for c in container.list_conversations_use_case.execute()
            ]
        )


class ConversationOperatorMessageView(APIView):
    """A human writes in the conversation (no LLM involved)."""

    def post(self, request, conversation_id):
        serializer = SendMessageSerializer(data=request.data)
        serializer.is_valid(raise_exception=True)
        container = get_app_conversation_container()
        try:
            detail = container.append_operator_message_use_case.execute(
                conversation_id, serializer.validated_data["content"]
            )
        except ConversationNotFoundError:
            return Response({"error": "Conversation not found"}, status=404)
        return Response(_detail_payload(detail))


class ConversationClientMessageView(APIView):
    """Reply as the customer: the real agent answers (unless a human took over)."""

    def post(self, request, conversation_id):
        serializer = SendMessageSerializer(data=request.data)
        serializer.is_valid(raise_exception=True)
        container = get_app_conversation_container()
        if container.reply_as_client_use_case is None:
            return Response(
                {"error": "The agent is not configured (missing the provider API key)."},
                status=503,
            )
        try:
            result = container.reply_as_client_use_case.execute(
                conversation_id, serializer.validated_data["content"]
            )
        except ConversationNotFoundError:
            return Response({"error": "Conversation not found"}, status=404)
        except Exception:
            logger.exception("Agent reply failed (conversation=%s)", conversation_id)
            return Response(
                {"error": "No pude procesar el mensaje en este momento. Reintentá."},
                status=502,
            )
        payload = _detail_payload(result.detail)
        payload["paused"] = result.paused
        payload["response"] = result.response
        return Response(payload)


class ConversationTakeoverView(APIView):
    def post(self, request, conversation_id):
        return _set_takeover(conversation_id, True)


class ConversationReleaseView(APIView):
    def post(self, request, conversation_id):
        return _set_takeover(conversation_id, False)


def _set_takeover(conversation_id, paused):
    container = get_app_conversation_container()
    try:
        detail = container.set_takeover_use_case.execute(conversation_id, paused)
    except ConversationNotFoundError:
        return Response({"error": "Conversation not found"}, status=404)
    return Response(_detail_payload(detail))


class AgentMessageView(APIView):
    """Agent entrypoint for channel drivers (Studio/HTTP now, WhatsApp later).

    The driver resolves identity: conversation from the thread, business from the
    request/config. The model never supplies them.
    """

    # Public: the WhatsApp bot bridge (customer-facing) calls this endpoint
    # without a staff JWT.
    permission_classes = [AllowAny]

    def post(self, request):
        serializer = AgentMessageSerializer(data=request.data)
        serializer.is_valid(raise_exception=True)
        data = serializer.validated_data

        from composition.container import resolve_agent_business_config_id

        business_id = resolve_agent_business_config_id(data.get("business_config_id"))

        container = get_app_conversation_container()
        if container.handle_incoming_message_use_case is None:
            return Response(
                {"error": "The agent is not configured (missing the provider API key)."},
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
            # Write operations require an idempotency id. The channel may supply
            # one; when it does not, generate it here (same rule as the LangGraph
            # driver) so mutations never fail for a missing id.
            external_message_id=data.get("external_message_id") or str(uuid.uuid4()),
        )

        try:
            result = container.handle_incoming_message_use_case.execute(
                HandleIncomingMessageCommand(context=context, content=data["content"])
            )
        except Exception:
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
