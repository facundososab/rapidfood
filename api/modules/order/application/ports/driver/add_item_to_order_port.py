from abc import ABC, abstractmethod
from dataclasses import dataclass, field
from typing import List, Optional, Tuple


@dataclass
class AddItemToOrderCommand:
    """Add an item to the order the caller already resolved as current.

    ``external_message_id`` is the stable per-ingress identity used for the
    idempotency key; the channel (LangChain/WhatsApp/HTTP) supplies it.
    """

    business_config_id: str
    order_id: str
    product_variant_id: str
    quantity: int
    external_message_id: str
    conversation_id: Optional[str] = None
    modifier_option_ids: List[str] = field(default_factory=list)
    removed_ingredient_ids: List[str] = field(default_factory=list)


@dataclass
class AddItemToOrderResponse:
    order_id: str
    line_id: str
    total_amount: str
    line_count: int
    version: int
    replayed: bool = False
    superseded_attempt_ids: Tuple[str, ...] = ()


class AddItemToOrderPort(ABC):
    @abstractmethod
    def execute(self, command: AddItemToOrderCommand) -> AddItemToOrderResponse:
        pass
