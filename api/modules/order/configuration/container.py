from typing import Any, Optional

from modules.order.application.use_cases.start_draft_order_use_case import StartDraftOrderUseCase
from modules.order.application.use_cases.add_line_use_case import AddLineUseCase
from modules.order.application.use_cases.update_line_quantity_use_case import UpdateLineQuantityUseCase
from modules.order.application.use_cases.remove_line_use_case import RemoveLineUseCase
from modules.order.application.use_cases.configure_order_use_case import ConfigureOrderUseCase
from modules.order.application.use_cases.confirm_order_use_case import ConfirmOrderUseCase
from modules.order.application.use_cases.apply_coupon_use_case import ApplyCouponUseCase
from modules.order.application.use_cases.cancel_order_use_case import CancelOrderUseCase
from modules.order.application.use_cases.advance_state_use_case import AdvanceStateUseCase
from modules.order.application.use_cases.get_order_use_case import GetOrderUseCase
from modules.order.application.use_cases.list_orders_use_case import ListOrdersUseCase
from modules.order.application.use_cases.update_order_status_use_case import (
    UpdateOrderStatusUseCase,
)
from modules.order.application.use_cases.create_payment_checkout_use_case import (
    CreatePaymentCheckoutUseCase,
)
from modules.order.application.use_cases.handle_payment_webhook_use_case import (
    HandlePaymentWebhookUseCase,
)
from modules.order.application.use_cases.cancel_superseded_checkout_use_case import (
    CancelSupersededCheckoutUseCase,
)
from modules.order.application.ports.driven.catalog_query import CatalogQuery
from modules.order.infrastructure.adapters.driven.mercadopago.mercadopago_payment_provider import (
    MercadoPagoPaymentProvider,
)
from modules.order.infrastructure.adapters.driven.mercadopago.mercadopago_settings import (
    MercadoPagoSettings,
)
from modules.order.infrastructure.adapters.driven.prisma.order_repository import (
    PrismaOrderRepository,
)
from modules.order.infrastructure.adapters.driven.prisma.payment_repository import (
    PrismaPaymentRepository,
)
from modules.order.infrastructure.adapters.driven.prisma.applied_coupon_repository import (
    PrismaAppliedCouponRepository,
)
from modules.order.application.use_cases.list_applied_coupons_use_case import (
    ListAppliedCouponsUseCase,
)
from modules.order.application.use_cases.add_item_to_order_use_case import (
    AddItemToOrderUseCase,
)
from modules.order.application.use_cases.update_item_in_order_use_case import (
    UpdateItemInOrderUseCase,
)
from modules.order.application.use_cases.remove_item_from_order_use_case import (
    RemoveItemFromOrderUseCase,
)
from modules.order.application.use_cases.set_payment_type_use_case import (
    SetPaymentTypeUseCase,
)
from modules.order.application.use_cases.set_client_for_order_use_case import (
    SetClientForOrderUseCase,
)
from modules.order.application.use_cases.set_delivery_for_order_use_case import (
    SetDeliveryForOrderUseCase,
)
from modules.order.application.use_cases.apply_coupon_to_order_use_case import (
    ApplyCouponToOrderUseCase,
)
from modules.order.application.use_cases.get_current_order_use_case import (
    GetCurrentOrderUseCase,
)
from modules.order.application.use_cases.get_latest_active_order_use_case import (
    GetLatestActiveOrderUseCase,
)
from modules.order.application.use_cases.get_order_summary_use_case import (
    GetOrderSummaryUseCase,
)
from modules.order.application.use_cases.set_pickup_for_order_use_case import (
    SetPickupForOrderUseCase,
)
from modules.order.application.use_cases.get_or_create_current_draft_use_case import (
    GetOrCreateCurrentDraftUseCase,
)
from modules.order.application.use_cases.get_preparation_time_configuration_use_case import (
    GetPreparationTimeConfigurationUseCase,
)
from modules.order.application.use_cases.configure_preparation_time_use_case import (
    ConfigurePreparationTimeUseCase,
)
from modules.order.infrastructure.adapters.driven.prisma.preparation_time_config_repository import (
    PrismaPreparationTimeConfigRepository,
)
from modules.order.infrastructure.adapters.driven.prisma.active_order_demand_query import (
    PrismaActiveOrderDemandQuery,
)
from modules.order.infrastructure.adapters.driven.prisma.preparation_time_estimator import (
    PreparationTimeEstimator,
)
from modules.order.infrastructure.adapters.driven.prisma.payment_attempt_query import (
    PrismaPaymentAttemptQuery,
)
from modules.order.infrastructure.adapters.driven.clock import SystemClock
from modules.order.infrastructure.adapters.driven.prisma.idempotent_order_mutation import (
    PrismaIdempotentOrderMutation,
)
from modules.order.infrastructure.adapters.driven.fakes.fakes import (
    FakeClientQuery, FakeCatalogQuery, FakeBusinessConfigQuery, FakeCouponQuery
)
from shared.infrastructure.prisma.db import db

class OrderContainer:
    """
    Dependency Injection Container for the Order module (ADR-Hexagonal).
    Wires driver ports (use cases) with driven ports (adapters).

    Cross-module driven ports (catalog, client, config, coupon) default to
    in-memory fakes; the app-level composition root injects the real adapters
    via the constructor.
    """

    def __init__(
        self,
        catalog_query: Optional[CatalogQuery] = None,
        client_query: Optional[Any] = None,
        config_query: Optional[Any] = None,
        coupon_query: Optional[Any] = None,
        coupon_consume: Optional[Any] = None,
        delivery_quote: Optional[Any] = None,
        prisma_client: Optional[Any] = None,
        paid_notifier: Optional[Any] = None,
    ):
        # Driven Adapters
        self.order_repository = PrismaOrderRepository()
        self.applied_coupon_repository = PrismaAppliedCouponRepository()
        self.payment_repository = PrismaPaymentRepository(prisma_client or db.client)
        self.mercadopago_settings = MercadoPagoSettings.from_env()
        self.payment_provider = MercadoPagoPaymentProvider(self.mercadopago_settings)

        # Preparation time (ETA): config + kitchen-load counter + estimator.
        self.preparation_time_config_repository = (
            PrismaPreparationTimeConfigRepository(db.client)
        )
        self.active_order_demand_query = PrismaActiveOrderDemandQuery(db.client)
        self.preparation_time_estimator = PreparationTimeEstimator(
            self.preparation_time_config_repository, self.active_order_demand_query
        )
        self.client_query = client_query if client_query is not None else FakeClientQuery()
        self.config_query = config_query if config_query is not None else FakeBusinessConfigQuery()
        self.coupon_query = coupon_query if coupon_query is not None else FakeCouponQuery()
        self.coupon_consume = coupon_consume
        self.delivery_quote = delivery_quote
        self.catalog_query = catalog_query if catalog_query is not None else FakeCatalogQuery()
        
        # Use Cases
        self.start_draft_order_use_case = StartDraftOrderUseCase(
            order_repo=self.order_repository,
            client_query=self.client_query
        )
        self.add_line_use_case = AddLineUseCase(
            order_repo=self.order_repository,
            catalog_query=self.catalog_query
        )
        self.update_line_quantity_use_case = UpdateLineQuantityUseCase(
            order_repo=self.order_repository,
            catalog_query=self.catalog_query
        )
        self.remove_line_use_case = RemoveLineUseCase(
            order_repo=self.order_repository
        )
        self.configure_order_use_case = ConfigureOrderUseCase(
            order_repo=self.order_repository,
            config_query=self.config_query,
            delivery_quote=self.delivery_quote,
            prep_time_estimator=self.preparation_time_estimator,
        )
        self.confirm_order_use_case = ConfirmOrderUseCase(
            order_repo=self.order_repository,
            config_query=self.config_query,
            catalog_query=self.catalog_query,
            coupon_consume=self.coupon_consume,
            prep_time_estimator=self.preparation_time_estimator,
        )
        self.apply_coupon_use_case = ApplyCouponUseCase(
            order_repo=self.order_repository,
            coupon_query=self.coupon_query,
            applied_coupon_repo=self.applied_coupon_repository
        )
        self.list_applied_coupons = ListAppliedCouponsUseCase(self.applied_coupon_repository)
        self.cancel_order_use_case = CancelOrderUseCase(
            order_repo=self.order_repository
        )
        self.advance_state_use_case = AdvanceStateUseCase(
            order_repo=self.order_repository
        )
        self.list_orders_use_case = ListOrdersUseCase(order_repo=self.order_repository)
        self.get_order_use_case = GetOrderUseCase(order_repo=self.order_repository)
        self.update_order_status = UpdateOrderStatusUseCase(
            order_repo=self.order_repository
        )
        self.create_payment_checkout_use_case = CreatePaymentCheckoutUseCase(
            order_repo=self.order_repository,
            payment_repo=self.payment_repository,
            payment_provider=self.payment_provider,
            currency=self.mercadopago_settings.currency,
        )
        self.handle_payment_webhook_use_case = HandlePaymentWebhookUseCase(
            order_repo=self.order_repository,
            payment_repo=self.payment_repository,
            payment_provider=self.payment_provider,
            paid_notifier=paid_notifier,
        )
        self.cancel_superseded_checkout_use_case = CancelSupersededCheckoutUseCase(
            payment_repo=self.payment_repository,
            payment_provider=self.payment_provider,
        )

        # Reopen-aware, idempotent mutations (agent / channel facing).
        clock = SystemClock()
        self.idempotent_order_mutation = PrismaIdempotentOrderMutation(db.client)
        self.add_item_to_order_use_case = AddItemToOrderUseCase(
            catalog_query=self.catalog_query,
            executor=self.idempotent_order_mutation,
            clock=clock,
        )
        self.update_item_in_order_use_case = UpdateItemInOrderUseCase(
            catalog_query=self.catalog_query,
            executor=self.idempotent_order_mutation,
            clock=clock,
        )
        self.remove_item_from_order_use_case = RemoveItemFromOrderUseCase(
            executor=self.idempotent_order_mutation,
            clock=clock,
        )
        self.set_payment_type_use_case = SetPaymentTypeUseCase(
            order_repo=self.order_repository
        )
        self.set_client_for_order_use_case = SetClientForOrderUseCase(
            order_repo=self.order_repository,
            client_query=self.client_query,
        )
        self.set_delivery_for_order_use_case = SetDeliveryForOrderUseCase(
            delivery_quote=self.delivery_quote,
            executor=self.idempotent_order_mutation,
            clock=clock,
            prep_time_estimator=self.preparation_time_estimator,
        )
        self.apply_coupon_to_order_use_case = ApplyCouponToOrderUseCase(
            coupon_query=self.coupon_query,
            executor=self.idempotent_order_mutation,
            clock=clock,
        )
        self.set_pickup_for_order_use_case = SetPickupForOrderUseCase(
            executor=self.idempotent_order_mutation,
            clock=clock,
            prep_time_estimator=self.preparation_time_estimator,
        )

        # Reads used by the agent / panel.
        payment_attempts = PrismaPaymentAttemptQuery(prisma_client or db.client)
        self.get_current_order_use_case = GetCurrentOrderUseCase(
            self.order_repository, payment_attempts
        )
        self.get_latest_active_order_use_case = GetLatestActiveOrderUseCase(
            self.order_repository
        )
        self.get_order_summary_use_case = GetOrderSummaryUseCase(
            self.order_repository, self.config_query, self.catalog_query
        )
        self.get_or_create_current_draft_use_case = GetOrCreateCurrentDraftUseCase(
            self.order_repository, self.start_draft_order_use_case
        )

        # Preparation time (ETA) configuration CRUD.
        self.get_preparation_time_configuration = (
            GetPreparationTimeConfigurationUseCase(
                self.preparation_time_config_repository
            )
        )
        self.configure_preparation_time = ConfigurePreparationTimeUseCase(
            self.preparation_time_config_repository
        )

_container: OrderContainer | None = None

def get_container() -> OrderContainer:
    global _container
    if _container is None:
        _container = OrderContainer()
    return _container
