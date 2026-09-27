from abc import ABC, abstractmethod
from dataclasses import dataclass
from typing import Optional, Tuple


@dataclass
class SetDeliveryForOrderCommand:
    business_config_id: str
    order_id: str
    external_message_id: str
    street: str
    street_number: str
    city: str
    province: str
    conversation_id: Optional[str] = None
    floor: Optional[str] = None
    apartment: Optional[str] = None
    postal_code: Optional[str] = None


@dataclass
class SetDeliveryForOrderResponse:
    order_id: str
    shipping_cost: str
    total_amount: str
    version: int
    replayed: bool = False
    superseded_attempt_ids: Tuple[str, ...] = ()


class SetDeliveryForOrderPort(ABC):
    @abstractmethod
    def execute(self, command: SetDeliveryForOrderCommand) -> SetDeliveryForOrderResponse:
        pass
