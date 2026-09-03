from typing import Optional

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
from modules.order.application.ports.driven.catalog_query import CatalogQuery
from modules.order.infrastructure.adapters.driven.prisma.order_repository import (
    PrismaOrderRepository,
)
from modules.order.infrastructure.adapters.driven.fakes.fakes import (
    FakeClientQuery, FakeCatalogQuery, FakeBusinessConfigQuery, FakeCouponQuery
)

class OrderContainer:
    """
    Dependency Injection Container for the Order module (ADR-Hexagonal).
    Wires driver ports (use cases) with driven ports (adapters).

    Cross-module driven ports (catalog, client, config, coupon) default to
    in-memory fakes; the app-level composition root injects the real adapters
    via the constructor.
    """

    def __init__(self, catalog_query: Optional[CatalogQuery] = None):
        # Driven Adapters
        self.order_repository = PrismaOrderRepository()
        self.client_query = FakeClientQuery()
        self.config_query = FakeBusinessConfigQuery()
        self.coupon_query = FakeCouponQuery()
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
            config_query=self.config_query
        )
        self.confirm_order_use_case = ConfirmOrderUseCase(
            order_repo=self.order_repository,
            config_query=self.config_query,
            catalog_query=self.catalog_query
        )
        self.apply_coupon_use_case = ApplyCouponUseCase(
            order_repo=self.order_repository,
            coupon_query=self.coupon_query
        )
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

# Singleton instance
_container = OrderContainer()

def get_container() -> OrderContainer:
    return _container
