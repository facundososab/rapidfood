from abc import ABC, abstractmethod
from dataclasses import dataclass
from datetime import datetime
from typing import List, Optional

from modules.order.domain.models.delivery_type import DeliveryType
from modules.order.domain.models.order import Order
from modules.order.domain.models.order_state import OrderState
from modules.order.domain.models.payment_method import PaymentMethod


@dataclass
class OrderFilter:
    status: Optional[OrderState] = None
    delivery_type: Optional[DeliveryType] = None
    payment_type: Optional[PaymentMethod] = None
    date_from: Optional[datetime] = None
    date_to: Optional[datetime] = None


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

    @abstractmethod
    def list(self, filter: Optional[OrderFilter] = None) -> List[Order]:
        """Retrieves orders matching the given filter, newest first."""
        pass
