from abc import ABC, abstractmethod
from dataclasses import dataclass
from decimal import Decimal


@dataclass
class BusinessConfigSnapshot:
    is_open: bool
    shipping_cost: Decimal
    min_order_amount: Decimal


class BusinessConfigQueryPort(ABC):
    @abstractmethod
    def get_config(self) -> BusinessConfigSnapshot:
        pass
