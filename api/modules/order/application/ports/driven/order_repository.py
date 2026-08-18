from abc import ABC, abstractmethod
from typing import Optional

from modules.order.domain.models.order import Order


class OrderRepository(ABC):
    """
    Port for Order persistence (driven).
    """

    @abstractmethod
    def save(self, order: Order) -> Order:
        """Creates or updates the order."""
        pass

    @abstractmethod
    def get_by_id(self, order_id: str) -> Optional[Order]:
        """Retrieves an order by its ID."""
        pass
