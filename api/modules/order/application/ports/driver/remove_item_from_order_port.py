from abc import ABC, abstractmethod
from dataclasses import dataclass
from typing import Optional, Tuple


@dataclass
class RemoveItemFromOrderCommand:
    business_config_id: str
    order_id: str
    line_id: str
    external_message_id: str
    conversation_id: Optional[str] = None


@dataclass
class RemoveItemFromOrderResponse:
    order_id: str
    line_count: int
    total_amount: str
    version: int
    replayed: bool = False
    superseded_attempt_ids: Tuple[str, ...] = ()


class RemoveItemFromOrderPort(ABC):
    @abstractmethod
    def execute(self, command: RemoveItemFromOrderCommand) -> RemoveItemFromOrderResponse:
        pass
