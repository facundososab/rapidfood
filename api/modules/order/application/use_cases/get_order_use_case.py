from typing import Optional

from modules.order.application.ports.driver.get_order_ports import GetOrderPort
from modules.order.application.ports.driven.order_repository import OrderRepository
from modules.order.domain.models.order import Order


class GetOrderUseCase(GetOrderPort):
    def __init__(self, order_repo: OrderRepository):
        self.order_repo = order_repo

    def execute(self, order_id: str) -> Optional[Order]:
        return self.order_repo.get_by_id(order_id)