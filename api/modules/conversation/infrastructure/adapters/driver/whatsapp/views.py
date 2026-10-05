"""WhatsApp channel driver: Meta webhook (verify + receive) and config REST.

Public webhook endpoints (Meta calls them, no staff JWT). The driver only does
CHANNEL work — authenticate the webhook, normalize the inbound (text/audio), and
deliver the reply — and delegates the turn itself to the channel-agnostic core
use case. Secrets live in the authenticator/adapters, never here.
"""
from __future__ import annotations

import json
import logging

from django.http import HttpResponse
from rest_framework.permissions import AllowAny
from rest_framework.response import Response
from rest_framework.views import APIView

from composition.container import get_app_conversation_container
from modules.conversation.application.ports.driver.whatsapp_config_ports import (
    GetWhatsAppConfigurationQuery,
    SaveWhatsAppConfigurationCommand,
)
from modules.conversation.application.ports.driver.whatsapp_messaging_ports import (
    SendConversationMessageCommand,
)
from modules.conversation.application.ports.driver.conversation_commands import (
    AddMessageCommand,
)
from modules.conversation.application.use_cases.handle_incoming_message import (
    HandleIncomingMessageCommand,
    message_id_for,
)
from modules.conversation.application.use_cases.resolve_conversation_for_channel import (
    ResolveConversationCommand,
)
from modules.conversation.domain.errors import WhatsAppConfigurationNotFoundError
from modules.conversation.domain.models.agent_execution_context import (
    AgentExecutionContext,
)
from modules.conversation.domain.value_objects import MessageRole
from modules.conversation.infrastructure.adapters.driver.whatsapp.serializers import (
    WhatsAppConfigSerializer,
)
from modules.conversation.infrastructure.adapters.driver.whatsapp.payload import (
    extract_contact_name,
    extract_metadata,
    parse_inbound_messages,
)

logger = logging.getLogger(__name__)

CHANNEL = "WHATSAPP"
AUDIO_FALLBACK = "No pude escuchar tu audio. ¿Me lo podés escribir, por favor?"
ERROR_FALLBACK = (
    "No pude procesar tu mensaje en este momento. ¿Podés reintentar en un rato?"
)


class WhatsAppWebhookView(APIView):
    # Meta does not send a JWT; skip auth and permission entirely.
    authentication_classes: list = []
    permission_classes = [AllowAny]

    def get(self, request):
        """Meta subscription handshake: echo hub.challenge on token match."""
        mode = request.query_params.get("hub.mode")
        token = request.query_params.get("hub.verify_token", "")
        challenge = request.query_params.get("hub.challenge", "")
        if mode == "subscribe" and token:
            container = get_app_conversation_container()
            authenticator = container.whatsapp_webhook_authenticator
            if authenticator is not None and authenticator.verify_subscription(token):
                return HttpResponse(challenge, content_type="text/plain")
        return HttpResponse(status=403)

    def post(self, request):
        raw_body = request.body
        try:
            payload = json.loads(raw_body or b"{}")
        except ValueError:
            logger.warning("WhatsApp webhook received invalid JSON")
            return HttpResponse(status=400)

        metadata = extract_metadata(payload)
        phone_number_id = metadata.phone_number_id
        if not phone_number_id:
            # Status updates / unrelated events: acknowledge and ignore.
            return HttpResponse(status=200)

        container = get_app_conversation_container()
        authenticator = container.whatsapp_webhook_authenticator
        if authenticator is None:
            logger.warning("WhatsApp webhook authenticator is not configured")
            return HttpResponse(status=200)

        identity = authenticator.resolve_identity(phone_number_id)
        if identity is None:
            logger.warning(
                "WhatsApp webhook from a number without config: "
                "phone_number_id=%s display_phone_number=%s. Put THIS "
                "phone_number_id in the panel, or message the number it targets.",
                phone_number_id,
                metadata.display_phone_number,
            )
            return HttpResponse(status=200)

        signature = request.META.get("HTTP_X_HUB_SIGNATURE_256", "")
        if not authenticator.verify_signature(phone_number_id, raw_body, signature):
            logger.warning(
                "WhatsApp webhook signature rejected (phone_number_id=%s)",
                phone_number_id,
            )
            return HttpResponse(status=403)

        contact_name = extract_contact_name(payload)
        for inbound in parse_inbound_messages(payload):
            try:
                _handle_inbound(
                    container, identity, phone_number_id, inbound, contact_name
                )
            except Exception:
                logger.exception(
                    "WhatsApp inbound handling failed (message=%s)", inbound.message_id
                )

        # Always 200: any other status makes Meta retry and duplicate the turn.
        return HttpResponse(status=200)


def _handle_inbound(
    container, identity, phone_number_id: str, inbound, contact_name: str | None = None
) -> None:
    # Link the customer: the phone is the identity, the WhatsApp display name is
    # what we can save for them. Best-effort and idempotent (find-or-create).
    client_id = None
    resolver = container.resolve_client_for_channel_use_case
    if resolver is not None:
        client_id = resolver.execute(contact_name, inbound.wa_id)

    resolution = container.resolve_conversation_use_case.execute(
        ResolveConversationCommand(
            business_config_id=identity.business_config_id,
            channel=CHANNEL,
            external_thread_id=inbound.wa_id,
            client_id=client_id,
        )
    )
    context = AgentExecutionContext(
        business_configuration_id=identity.business_config_id,
        conversation_id=resolution.conversation_id,
        channel=CHANNEL,
        client_id=resolution.client_id,
        external_thread_id=inbound.wa_id,
        external_message_id=inbound.message_id,
    )

    content = inbound.text
    if content is None and inbound.audio_media_id:
        content = _transcribe_audio(container, phone_number_id, inbound)

    if content is None:
        # Untranscribable audio: keep it in the panel. The bot's fallback is only
        # suppressed when a human owns the conversation (resolution tells us).
        _persist_inbound_message(container, context, "[audio]")
        if not resolution.agent_paused:
            _send_reply_safe(container, resolution.conversation_id, AUDIO_FALLBACK)
        return

    handler = container.handle_incoming_message_use_case
    if handler is None:
        logger.warning("Agent not configured; WhatsApp message stored only.")
        return

    try:
        result = handler.execute(
            HandleIncomingMessageCommand(context=context, content=content)
        )
    except Exception:
        # The agent/tools failed. Never explode the webhook: apologize and keep
        # going (the USER message is already persisted by the handler).
        logger.exception("Agent turn failed (conversation=%s)", context.conversation_id)
        _send_reply_safe(container, resolution.conversation_id, ERROR_FALLBACK)
        return

    # The turn policy (retry dedup + human takeover) lives in the use case; the
    # driver only decides whether to deliver a reply.
    if result.already_processed:
        logger.info("Duplicate WhatsApp delivery ignored (message=%s)", inbound.message_id)
        return
    if result.paused:
        logger.info(
            "Conversation paused; the agent stayed silent (message=%s)",
            inbound.message_id,
        )
        return

    _send_reply_safe(container, resolution.conversation_id, result.response)


def _transcribe_audio(container, phone_number_id: str, inbound) -> str | None:
    transcriber = container.whatsapp_inbound_audio_transcriber
    if transcriber is None:
        logger.warning("Audio transcription is not configured; using fallback.")
        return None
    try:
        return transcriber.transcribe(
            phone_number_id,
            inbound.audio_media_id,
            inbound.audio_mime_type,
        )
    except Exception:
        logger.exception("Audio transcription raised unexpectedly")
        return None


def _persist_inbound_message(container, context, content) -> None:
    """Store an inbound that will NOT be answered by the agent (paused/audio)."""
    if container.add_message_use_case is None or not content:
        return
    try:
        container.add_message_use_case.execute(
            AddMessageCommand(
                message_id=message_id_for(context),
                conversation_id=context.conversation_id,
                role=MessageRole.USER,
                content=content,
            )
        )
    except Exception:
        logger.exception("Failed to persist the inbound message")


def _send_reply_safe(container, conversation_id: str, content: str) -> None:
    """Best-effort channel delivery.

    A delivery failure (e.g. Meta 131030 "recipient not in allowed list" while the
    test number is used) is logged as a warning, not raised: the reply is already
    stored in the panel and must not 500 the webhook or hide the conversation.
    """
    use_case = container.send_conversation_message_use_case
    if use_case is None:
        return
    try:
        use_case.execute(
            SendConversationMessageCommand(
                conversation_id=conversation_id, content=content
            )
        )
    except Exception as exc:
        logger.warning("WhatsApp reply delivery failed: %s", exc)


class WhatsAppConfigurationView(APIView):
    """Staff-only GET/PUT of the business WhatsApp credentials (secrets masked)."""

    def get(self, request):
        business_config_id = request.query_params.get(
            "business_config_id", "default"
        )
        container = get_app_conversation_container()
        try:
            view = container.get_whatsapp_configuration_use_case.execute(
                GetWhatsAppConfigurationQuery(business_config_id=business_config_id)
            )
        except WhatsAppConfigurationNotFoundError:
            return Response({"configured": False})
        payload = _serialize_view(view)
        payload["configured"] = True
        return Response(payload)

    def put(self, request):
        serializer = WhatsAppConfigSerializer(data=request.data)
        serializer.is_valid(raise_exception=True)
        container = get_app_conversation_container()
        view = container.save_whatsapp_configuration_use_case.execute(
            SaveWhatsAppConfigurationCommand(**serializer.validated_data)
        )
        payload = _serialize_view(view)
        payload["configured"] = True
        return Response(payload)


def _serialize_view(view) -> dict:
    return {
        "business_config_id": view.business_config_id,
        "phone_number_id": view.phone_number_id,
        "verify_token": view.verify_token,
        "api_version": view.api_version,
        "waba_id": view.waba_id,
        "display_phone_number": view.display_phone_number,
        "order_paid_template_name": view.order_paid_template_name,
        "order_paid_template_lang": view.order_paid_template_lang,
        "is_active": view.is_active,
        "has_access_token": view.has_access_token,
        "has_app_secret": view.has_app_secret,
    }
