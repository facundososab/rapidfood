from abc import ABC, abstractmethod
from dataclasses import dataclass
from typing import Optional, Tuple


@dataclass
class SetPickupForOrderCommand:
    business_config_id: str
    order_id: str
    external_message_id: str
    conversation_id: Optional[str] = None


@dataclass
class SetPickupForOrderResponse:
    order_id: str
    version: int
    replayed: bool = False
    superseded_attempt_ids: Tuple[str, ...] = ()


class SetPickupForOrderPort(ABC):
    @abstractmethod
    def execute(self, command: SetPickupForOrderCommand) -> SetPickupForOrderResponse:
        pass
