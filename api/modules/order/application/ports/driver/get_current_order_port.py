from abc import ABC, abstractmethod
from dataclasses import dataclass
from typing import Optional

from modules.order.domain.models.order import Order


@dataclass
class GetCurrentOrderQuery:
    business_config_id: str
    conversation_id: str


@dataclass
class CurrentOrderResult:
    """Read-only resolution of the order a conversation is working on.

    Never mutates: ``requires_reopen`` tells the caller a mutation would reopen
    the pending online order, and ``requires_new_order`` that a new order is
    needed for a new purchase intent.
    """

    found: bool
    order: Optional[Order]
    editable: bool = False
    requires_reopen: bool = False
    requires_new_order: bool = False


class GetCurrentOrderPort(ABC):
    @abstractmethod
    def execute(self, query: GetCurrentOrderQuery) -> CurrentOrderResult:
        pass
