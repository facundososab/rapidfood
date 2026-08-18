from abc import ABC, abstractmethod
from dataclasses import dataclass
from typing import Optional


@dataclass
class SetDeliveryDetailsCommand:
    order_id: str
    delivery_type: str
    address_id: Optional[str] = None


@dataclass
class SetDeliveryDetailsResponse:
    order_id: str
    shipping_cost: str
    total_amount: str


class ConfigureOrderPort(ABC):
    @abstractmethod
    def set_delivery_details(self, command: SetDeliveryDetailsCommand) -> SetDeliveryDetailsResponse:
        pass
