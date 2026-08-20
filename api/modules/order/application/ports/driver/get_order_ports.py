from abc import ABC, abstractmethod
from typing import Optional

from modules.order.domain.models.order import Order


class GetOrderPort(ABC):
    @abstractmethod
    def execute(self, order_id: str) -> Optional[Order]:
        pass