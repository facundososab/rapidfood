from abc import ABC, abstractmethod
from dataclasses import dataclass
from typing import Optional


@dataclass
class SetDeliveryDetailsCommand:
    order_id: str
    delivery_type: str
    address_id: Optional[str] = None
    # Delivery destination snapshot (required when delivery_type == DELIVERY).
    street: Optional[str] = None
    street_number: Optional[str] = None
    floor: Optional[str] = None
    apartment: Optional[str] = None
    city: Optional[str] = None
    province: Optional[str] = None
    postal_code: Optional[str] = None


@dataclass
class SetDeliveryDetailsResponse:
    order_id: str
    shipping_cost: str
    total_amount: str


class ConfigureOrderPort(ABC):
    @abstractmethod
    def set_delivery_details(self, command: SetDeliveryDetailsCommand) -> SetDeliveryDetailsResponse:
        pass
