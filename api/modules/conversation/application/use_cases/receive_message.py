from __future__ import annotations

from uuid import uuid4

from api.modules.conversation.application.ports.driver.conversation_commands import (
    AddMessageCommand,
    GetOrCreateConversationCommand,
    ReceiveMessageCommand,
)
from api.modules.conversation.application.ports.driver.conversation_responses import ReceiveMessageResult
from api.modules.conversation.application.ports.driven.clock import ClockPort
from api.modules.conversation.application.ports.driven.conversation_repository import ConversationRepositoryPort
from api.modules.conversation.application.ports.driven.cross_module import (
    BusinessConfigurationPort,
    CatalogProductQueryPort,
    ClientIdentityPort,
    CouponValidationPort,
    OrderDraftPort,
)
from api.modules.conversation.application.ports.driven.intent_detector import IntentDetectorPort
from api.modules.conversation.application.ports.driven.message_repository import MessageRepositoryPort
from api.modules.conversation.application.use_cases.add_message import AddMessageUseCase
from api.modules.conversation.application.use_cases.get_or_create_conversation import GetOrCreateConversationUseCase
from api.modules.conversation.domain.value_objects import DetectedIntent, MessageRole, MessageStatus


class ReceiveMessageUseCase:
    def __init__(
        self,
        conversation_repository: ConversationRepositoryPort,
        message_repository: MessageRepositoryPort,
        intent_detector: IntentDetectorPort,
        clock: ClockPort,
        order_draft_port: OrderDraftPort | None = None,
        client_identity_port: ClientIdentityPort | None = None,
        catalog_product_query_port: CatalogProductQueryPort | None = None,
        business_configuration_port: BusinessConfigurationPort | None = None,
        coupon_validation_port: CouponValidationPort | None = None,
    ):
        self._conversation_repository = conversation_repository
        self._message_repository = message_repository
        self._intent_detector = intent_detector
        self._clock = clock
        self._order_draft_port = order_draft_port
        self._client_identity_port = client_identity_port
        self._catalog_product_query_port = catalog_product_query_port
        self._business_configuration_port = business_configuration_port
        self._coupon_validation_port = coupon_validation_port

    def execute(self, command: ReceiveMessageCommand) -> ReceiveMessageResult:
        get_or_create = GetOrCreateConversationUseCase(self._conversation_repository)
        conversation_result = get_or_create.execute(
            GetOrCreateConversationCommand(
                channel=command.channel,
                channel_identity=command.channel_identity,
                client_id=self._resolve_client_id(command.channel, command.channel_identity),
            )
        )
        conversation_id = conversation_result.conversation.conversation_id

        user_message = AddMessageUseCase(self._message_repository, self._clock).execute(
            AddMessageCommand(
                message_id=command.external_message_id or str(uuid4()),
                conversation_id=conversation_id,
                role=MessageRole.USER,
                content=command.content,
                detected_intent=None,
                sentiment=None,
                status=MessageStatus.RECEIVED,
            )
        ).message

        intent = self._intent_detector.detect(command.content)
        self._conversation_repository.save_last_intent(conversation_id, intent)

        response = self._build_response(intent, conversation_id, command)

        agent_message = AddMessageUseCase(self._message_repository, self._clock).execute(
            AddMessageCommand(
                message_id=str(uuid4()),
                conversation_id=conversation_id,
                role=MessageRole.AGENT,
                content=response,
                detected_intent=intent,
                sentiment=None,
                status=MessageStatus.PROCESSED,
            )
        ).message

        return ReceiveMessageResult(
            conversation_id=conversation_id,
            user_message_id=user_message.message_id,
            agent_message_id=agent_message.message_id,
            intent=intent,
            response=response,
        )

    def _resolve_client_id(self, channel: str, channel_identity: str) -> str | None:
        if self._client_identity_port is None:
            return None
        return self._client_identity_port.resolve_client_id(channel, channel_identity)

    def _build_response(self, intent: DetectedIntent, conversation_id: str, command: ReceiveMessageCommand) -> str:
        self._touch_order_support(intent, command)

        if intent is DetectedIntent.START_ORDER:
            if self._order_draft_port is not None:
                active = self._order_draft_port.find_active_draft(conversation_id)
                if active is not None:
                    return "Tenés un borrador activo. ¿Querés seguir con ese pedido o empezar de nuevo?"
                self._order_draft_port.create_draft(
                    conversation_id,
                    self._resolve_client_id(command.channel, command.channel_identity),
                )
            return "Dale, arranquemos con tu pedido."

        if intent is DetectedIntent.CONFIRM_ORDER:
            if not _is_explicit_confirmation(command.content):
                return "Necesito una confirmación explícita para avanzar con el pedido."
            if self._order_draft_port is not None:
                active = self._order_draft_port.find_active_draft(conversation_id)
                if active is not None:
                    draft_id = active.get("draft_id") if isinstance(active, dict) else getattr(active, "draft_id", None)
                    if draft_id is not None:
                        self._order_draft_port.confirm_draft(conversation_id, draft_id)
            return "Perfecto, estoy confirmando tu pedido."

        if intent is DetectedIntent.MODIFY_ORDER:
            return "Dale, decime qué querés cambiar del pedido."

        if intent is DetectedIntent.QUERY_DRAFT:
            return "Te muestro el estado del borrador."

        if intent is DetectedIntent.QUERY_ORDER:
            return "Te cuento el estado de tu pedido."

        return "Te leo."

    def _touch_order_support(self, intent: DetectedIntent, command: ReceiveMessageCommand) -> None:
        if intent not in {
            DetectedIntent.START_ORDER,
            DetectedIntent.CONFIRM_ORDER,
            DetectedIntent.MODIFY_ORDER,
        }:
            return

        if self._catalog_product_query_port is not None and intent is DetectedIntent.START_ORDER:
            self._catalog_product_query_port.search_products(command.content)

        if self._business_configuration_port is not None:
            self._business_configuration_port.is_business_open(self._clock.now())

        coupon_code = _extract_coupon_code(command.content)
        if self._coupon_validation_port is not None and coupon_code is not None:
            self._coupon_validation_port.validate_coupon(coupon_code, self._resolve_client_id(command.channel, command.channel_identity))


def _is_explicit_confirmation(content: str) -> bool:
    normalized = content.strip().lower()
    return normalized in {"confirmo", "sí confirmo", "si confirmo", "confirmar", "dale confirmo"} or "confirmo" in normalized


def _extract_coupon_code(content: str) -> str | None:
    normalized = content.strip().lower()
    for marker in ("cupon", "cupón", "coupon"):
        if marker in normalized:
            parts = normalized.split(marker, maxsplit=1)
            candidate = parts[1].strip(" :,-") if len(parts) > 1 else ""
            return candidate.split()[0] if candidate else marker
    return None
