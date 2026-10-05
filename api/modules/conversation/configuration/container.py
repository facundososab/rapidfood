from __future__ import annotations

from dataclasses import dataclass
from typing import Callable, Optional

from modules.conversation.application.ports.driven.agent_runner import (
    AgentRunnerPort,
)
from modules.conversation.application.ports.driven.business_service import (
    BusinessServicePort,
)
from modules.conversation.application.ports.driven.catalog_service import (
    CatalogServicePort,
)
from modules.conversation.application.ports.driven.client_service import (
    ClientServicePort,
)
from modules.conversation.application.ports.driven.delivery_service import (
    DeliveryServicePort,
)
from modules.conversation.application.ports.driven.order_service import (
    OrderServicePort,
)
from modules.conversation.application.ports.driven.outbound_message import (
    OutboundMessagePort,
)
from modules.conversation.application.use_cases.add_message import AddMessageUseCase
from modules.conversation.application.use_cases.catalog_queries import (
    GetProductDetailForConversationUseCase,
    SearchProductsForConversationUseCase,
)
from modules.conversation.application.use_cases.delivery import (
    QuoteDeliveryForConversationUseCase,
)
from modules.conversation.application.use_cases.get_or_create_conversation import (
    GetOrCreateConversationUseCase,
)
from modules.conversation.application.use_cases.handle_incoming_message import (
    HandleIncomingMessageUseCase,
)
from modules.conversation.application.use_cases.list_messages import ListMessagesUseCase
from modules.conversation.application.use_cases.notify_order_paid import (
    NotifyOrderPaidUseCase,
)
from modules.conversation.application.use_cases.order_mutations import (
    AddItemToConversationOrderUseCase,
    ApplyCouponForConversationOrderUseCase,
    CancelConversationOrderUseCase,
    ConfirmConversationOrderUseCase,
    CreateCheckoutForConversationOrderUseCase,
    RemoveItemFromConversationOrderUseCase,
    SetDeliveryForConversationOrderUseCase,
    SetClientForConversationOrderUseCase,
    SetPaymentTypeForConversationOrderUseCase,
    SetPickupForConversationOrderUseCase,
    UpdateItemInConversationOrderUseCase,
)
from modules.conversation.application.use_cases.order_reads import (
    GetCurrentOrderForConversationUseCase,
    GetLatestActiveOrderForConversationUseCase,
    GetOrderSummaryForConversationUseCase,
)
from modules.conversation.application.use_cases.panel_conversations import (
    AppendOperatorMessageUseCase,
    GetConversationDetailUseCase,
    ListConversationsUseCase,
    ReplyAsClientForConversationUseCase,
    SetConversationTakeoverUseCase,
)
from modules.conversation.application.use_cases.receive_message import ReceiveMessageUseCase
from modules.conversation.application.use_cases.resolve_conversation_for_channel import (
    ResolveConversationForChannelUseCase,
)
from modules.conversation.application.use_cases.get_whatsapp_configuration import (
    GetWhatsAppConfigurationUseCase,
)
from modules.conversation.application.use_cases.save_whatsapp_configuration import (
    SaveWhatsAppConfigurationUseCase,
)
from modules.conversation.application.use_cases.resolve_client_for_channel import (
    ResolveClientForChannelUseCase,
)
from modules.conversation.application.use_cases.send_conversation_message import (
    SendConversationMessageUseCase,
)
from modules.conversation.infrastructure.adapters.driven.clock import SystemClock
from modules.conversation.infrastructure.adapters.driven.outbound.dev_outbound_message_adapter import (
    DevOutboundMessageAdapter,
)
from modules.conversation.infrastructure.adapters.driven.intent.deterministic_intent_detector import (
    DeterministicIntentDetector,
)
from modules.conversation.infrastructure.adapters.driven.prisma.conversation_repository import (
    PrismaConversationRepository,
)
from modules.conversation.infrastructure.adapters.driven.prisma.message_repository import (
    PrismaMessageRepository,
)
from modules.conversation.infrastructure.adapters.driven.prisma.whatsapp_configuration_repository import (
    PrismaWhatsAppConfigurationRepository,
)
from modules.conversation.infrastructure.adapters.driven.whatsapp.whatsapp_cloud_client import (
    WhatsAppCloudClient,
)
from modules.conversation.infrastructure.adapters.driven.whatsapp.whatsapp_outbound_message_adapter import (
    WhatsAppOutboundMessageAdapter,
)
from modules.conversation.infrastructure.adapters.driven.whatsapp.whatsapp_inbound_audio_transcriber import (
    WhatsAppInboundAudioTranscriber,
)
from modules.conversation.infrastructure.adapters.driven.whatsapp.whatsapp_webhook_authenticator import (
    WhatsAppWebhookAuthenticator,
)


@dataclass(slots=True)
class ConversationContainer:
    # Persistence + channel resolution
    resolve_conversation_use_case: ResolveConversationForChannelUseCase
    get_or_create_conversation_use_case: GetOrCreateConversationUseCase
    add_message_use_case: AddMessageUseCase
    list_messages_use_case: ListMessagesUseCase
    receive_message_use_case: ReceiveMessageUseCase
    # Set when an agent runner is injected (LangChain/LangGraph driver).
    handle_incoming_message_use_case: Optional[HandleIncomingMessageUseCase] = None
    # Panel chat (list, human takeover, reply as the customer).
    list_conversations_use_case: Optional[ListConversationsUseCase] = None
    get_conversation_detail_use_case: Optional[GetConversationDetailUseCase] = None
    append_operator_message_use_case: Optional[AppendOperatorMessageUseCase] = None
    set_takeover_use_case: Optional[SetConversationTakeoverUseCase] = None
    reply_as_client_use_case: Optional[ReplyAsClientForConversationUseCase] = None

    # Agent use cases (built when the cross-module services are injected).
    search_products_use_case: Optional[SearchProductsForConversationUseCase] = None
    get_product_detail_use_case: Optional[GetProductDetailForConversationUseCase] = None
    get_current_order_use_case: Optional[GetCurrentOrderForConversationUseCase] = None
    add_item_use_case: Optional[AddItemToConversationOrderUseCase] = None
    update_item_use_case: Optional[UpdateItemInConversationOrderUseCase] = None
    remove_item_use_case: Optional[RemoveItemFromConversationOrderUseCase] = None
    quote_delivery_use_case: Optional[QuoteDeliveryForConversationUseCase] = None
    set_delivery_use_case: Optional[SetDeliveryForConversationOrderUseCase] = None
    set_pickup_use_case: Optional[SetPickupForConversationOrderUseCase] = None
    set_client_use_case: Optional[SetClientForConversationOrderUseCase] = None
    set_payment_type_use_case: Optional[SetPaymentTypeForConversationOrderUseCase] = None
    apply_coupon_use_case: Optional[ApplyCouponForConversationOrderUseCase] = None
    get_order_summary_use_case: Optional[GetOrderSummaryForConversationUseCase] = None
    confirm_order_use_case: Optional[ConfirmConversationOrderUseCase] = None
    cancel_order_use_case: Optional[CancelConversationOrderUseCase] = None
    get_latest_active_order_use_case: Optional[GetLatestActiveOrderForConversationUseCase] = None
    create_checkout_use_case: Optional[CreateCheckoutForConversationOrderUseCase] = None
    notify_order_paid_use_case: Optional[NotifyOrderPaidUseCase] = None

    # WhatsApp channel: per-business credentials + delivery.
    get_whatsapp_configuration_use_case: Optional[
        GetWhatsAppConfigurationUseCase
    ] = None
    save_whatsapp_configuration_use_case: Optional[
        SaveWhatsAppConfigurationUseCase
    ] = None
    resolve_client_for_channel_use_case: Optional[ResolveClientForChannelUseCase] = None
    send_conversation_message_use_case: Optional[SendConversationMessageUseCase] = None
    # Channel infrastructure (NOT application use cases): the driver uses these
    # through the container and they own the WhatsApp credentials.
    whatsapp_webhook_authenticator: Optional[WhatsAppWebhookAuthenticator] = None
    whatsapp_inbound_audio_transcriber: Optional[WhatsAppInboundAudioTranscriber] = None


def build_container(
    catalog_service: Optional[CatalogServicePort] = None,
    order_service: Optional[OrderServicePort] = None,
    delivery_service: Optional[DeliveryServicePort] = None,
    business_service: Optional[BusinessServicePort] = None,
    client_service: Optional[ClientServicePort] = None,
    conversation_repository=None,
    message_repository=None,
    agent_runner_factory: Optional[Callable[["ConversationContainer"], AgentRunnerPort]] = None,
    outbound_message: Optional[OutboundMessagePort] = None,
    whatsapp_config_repository=None,
    whatsapp_sender=None,
    whatsapp_media=None,
    transcriber=None,
    whatsapp_outbound: bool = False,
) -> ConversationContainer:
    """Build the conversation module wiring.

    No I/O happens here: the Prisma repositories resolve their client lazily, so
    importing the URLs / building the container never opens a connection.
    Cross-module services are injected by the app-level composition root;
    repositories can be overridden with in-memory fakes in tests.
    """
    conversation_repository = conversation_repository or PrismaConversationRepository()
    message_repository = message_repository or PrismaMessageRepository()
    whatsapp_config_repository = (
        whatsapp_config_repository or PrismaWhatsAppConfigurationRepository()
    )
    whatsapp_sender = whatsapp_sender or WhatsAppCloudClient()
    whatsapp_media = whatsapp_media or whatsapp_sender
    clock = SystemClock()
    intent_detector = DeterministicIntentDetector()
    # Default outbound channel: dev adapter (logs + persists) so tests and local
    # runs never hit Meta. Production wiring opts into the real WhatsApp sender.
    if outbound_message is None:
        if whatsapp_outbound:
            outbound_message = WhatsAppOutboundMessageAdapter(
                whatsapp_sender,
                whatsapp_config_repository,
                conversation_repository,
                message_repository,
                clock,
            )
        else:
            outbound_message = DevOutboundMessageAdapter()

    container = ConversationContainer(
        resolve_conversation_use_case=ResolveConversationForChannelUseCase(
            conversation_repository
        ),
        get_or_create_conversation_use_case=GetOrCreateConversationUseCase(
            conversation_repository
        ),
        add_message_use_case=AddMessageUseCase(message_repository, clock),
        list_messages_use_case=ListMessagesUseCase(message_repository),
        receive_message_use_case=ReceiveMessageUseCase(
            conversation_repository, message_repository, intent_detector, clock
        ),
    )

    container.get_whatsapp_configuration_use_case = GetWhatsAppConfigurationUseCase(
        whatsapp_config_repository
    )
    container.save_whatsapp_configuration_use_case = (
        SaveWhatsAppConfigurationUseCase(whatsapp_config_repository)
    )
    container.resolve_client_for_channel_use_case = ResolveClientForChannelUseCase(
        client_service
    )
    container.send_conversation_message_use_case = SendConversationMessageUseCase(
        conversation_repository, outbound_message
    )
    # Channel infrastructure: owns WhatsApp credentials; used by the driver.
    container.whatsapp_webhook_authenticator = WhatsAppWebhookAuthenticator(
        whatsapp_config_repository
    )
    if transcriber is not None:
        container.whatsapp_inbound_audio_transcriber = WhatsAppInboundAudioTranscriber(
            whatsapp_config_repository, whatsapp_media, transcriber
        )

    container.list_conversations_use_case = ListConversationsUseCase(
        conversation_repository, message_repository, client_service
    )
    container.get_conversation_detail_use_case = GetConversationDetailUseCase(
        conversation_repository, message_repository, client_service
    )
    container.append_operator_message_use_case = AppendOperatorMessageUseCase(
        conversation_repository,
        message_repository,
        clock,
        send_message=container.send_conversation_message_use_case,
    )
    container.set_takeover_use_case = SetConversationTakeoverUseCase(
        conversation_repository, message_repository
    )

    if agent_runner_factory is not None:
        handler = HandleIncomingMessageUseCase(
            message_repository,
            agent_runner_factory(container),
            clock,
            conversation_repository=conversation_repository,
        )
        container.handle_incoming_message_use_case = handler
        container.reply_as_client_use_case = ReplyAsClientForConversationUseCase(
            conversation_repository,
            message_repository,
            handler,
            clock,
            send_message=container.send_conversation_message_use_case,
        )

    if catalog_service is not None:
        container.search_products_use_case = SearchProductsForConversationUseCase(
            catalog_service
        )
        container.get_product_detail_use_case = GetProductDetailForConversationUseCase(
            catalog_service
        )

    if delivery_service is not None:
        container.quote_delivery_use_case = QuoteDeliveryForConversationUseCase(
            delivery_service, business_service
        )

    if order_service is not None:
        container.get_current_order_use_case = GetCurrentOrderForConversationUseCase(
            order_service
        )
        container.get_latest_active_order_use_case = (
            GetLatestActiveOrderForConversationUseCase(order_service)
        )
        container.get_order_summary_use_case = GetOrderSummaryForConversationUseCase(
            order_service
        )
        container.add_item_use_case = AddItemToConversationOrderUseCase(order_service)
        container.update_item_use_case = UpdateItemInConversationOrderUseCase(
            order_service
        )
        container.remove_item_use_case = RemoveItemFromConversationOrderUseCase(
            order_service
        )
        container.set_delivery_use_case = SetDeliveryForConversationOrderUseCase(
            order_service, business_service
        )
        container.set_pickup_use_case = SetPickupForConversationOrderUseCase(order_service)
        container.set_client_use_case = SetClientForConversationOrderUseCase(
            order_service, client_service
        )
        container.set_payment_type_use_case = SetPaymentTypeForConversationOrderUseCase(
            order_service
        )
        container.apply_coupon_use_case = ApplyCouponForConversationOrderUseCase(
            order_service
        )
        container.confirm_order_use_case = ConfirmConversationOrderUseCase(order_service)
        container.cancel_order_use_case = CancelConversationOrderUseCase(order_service)
        container.create_checkout_use_case = CreateCheckoutForConversationOrderUseCase(
            order_service
        )
        container.notify_order_paid_use_case = NotifyOrderPaidUseCase(
            order_service,
            conversation_repository,
            message_repository,
            outbound_message,
            clock,
        )

    return container
