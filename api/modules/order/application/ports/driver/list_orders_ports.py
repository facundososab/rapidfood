from abc import ABC, abstractmethod
from dataclasses import dataclass
from datetime import datetime
from typing import List, Optional

from modules.order.domain.models.order import Order


@dataclass
class ListOrdersQuery:
    status: Optional[str] = None
    delivery_type: Optional[str] = None
    payment_type: Optional[str] = None
    search: Optional[str] = None
    date_from: Optional[datetime] = None
    date_to: Optional[datetime] = None


class ListOrdersPort(ABC):
    @abstractmethod
    def execute(self, query: ListOrdersQuery) -> List[Order]:
        pass