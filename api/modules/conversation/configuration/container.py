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
from modules.conversation.infrastructure.adapters.driven.clock import SystemClock
from modules.conversation.infrastructure.adapters.driven.intent.deterministic_intent_detector import (
    DeterministicIntentDetector,
)
from modules.conversation.infrastructure.adapters.driven.prisma.conversation_repository import (
    PrismaConversationRepository,
)
from modules.conversation.infrastructure.adapters.driven.prisma.message_repository import (
    PrismaMessageRepository,
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


def build_container(
    catalog_service: Optional[CatalogServicePort] = None,
    order_service: Optional[OrderServicePort] = None,
    delivery_service: Optional[DeliveryServicePort] = None,
    business_service: Optional[BusinessServicePort] = None,
    client_service: Optional[ClientServicePort] = None,
    conversation_repository=None,
    message_repository=None,
    agent_runner_factory: Optional[Callable[["ConversationContainer"], AgentRunnerPort]] = None,
) -> ConversationContainer:
    """Build the conversation module wiring.

    No I/O happens here: the Prisma repositories resolve their client lazily, so
    importing the URLs / building the container never opens a connection.
    Cross-module services are injected by the app-level composition root;
    repositories can be overridden with in-memory fakes in tests.
    """
    conversation_repository = conversation_repository or PrismaConversationRepository()
    message_repository = message_repository or PrismaMessageRepository()
    clock = SystemClock()
    intent_detector = DeterministicIntentDetector()

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

    container.list_conversations_use_case = ListConversationsUseCase(
        conversation_repository, message_repository, client_service
    )
    container.get_conversation_detail_use_case = GetConversationDetailUseCase(
        conversation_repository, message_repository, client_service
    )
    container.append_operator_message_use_case = AppendOperatorMessageUseCase(
        conversation_repository, message_repository, clock
    )
    container.set_takeover_use_case = SetConversationTakeoverUseCase(
        conversation_repository, message_repository
    )

    if agent_runner_factory is not None:
        handler = HandleIncomingMessageUseCase(
            message_repository, agent_runner_factory(container), clock
        )
        container.handle_incoming_message_use_case = handler
        container.reply_as_client_use_case = ReplyAsClientForConversationUseCase(
            conversation_repository, message_repository, handler, clock
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

    return container
