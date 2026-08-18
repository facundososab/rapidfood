from typing import List

from modules.order.application.ports.driver.list_orders_ports import (
    ListOrdersPort,
    ListOrdersQuery,
)
from modules.order.application.ports.driven.order_repository import (
    OrderFilter,
    OrderRepository,
)
from modules.order.domain.errors.order_errors import OrderStateError
from modules.order.domain.models.delivery_type import DeliveryType
from modules.order.domain.models.order import Order
from modules.order.domain.models.order_state import OrderState
from modules.order.domain.models.payment_method import PaymentMethod


class ListOrdersUseCase(ListOrdersPort):
    def __init__(self, order_repo: OrderRepository):
        self.order_repo = order_repo

    def execute(self, query: ListOrdersQuery) -> List[Order]:
        orders = self.order_repo.list(
            OrderFilter(
                status=self._optional_enum(OrderState, query.status),
                delivery_type=self._optional_enum(DeliveryType, query.delivery_type),
                payment_type=self._optional_enum(PaymentMethod, query.payment_type),
                date_from=query.date_from,
                date_to=query.date_to,
            )
        )
        if query.search:
            needle = query.search.lower().strip()
            orders = [o for o in orders if needle in o.id.lower()]
        return orders

    @staticmethod
    def _optional_enum(enum_cls, value):
        if value in (None, ""):
            return None
        try:
            return enum_cls(value)
        except ValueError:
            raise OrderStateError(f"'{value}' is not a valid order filter value")