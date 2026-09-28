from abc import ABC, abstractmethod
from dataclasses import dataclass, field
from typing import List, Optional, Tuple


@dataclass
class UpdateItemInOrderCommand:
    """Update an existing order line, identified by ``line_id``.

    ``None`` means "leave unchanged"; an empty list means "clear". Modifiers and
    removed ingredients are validated against the catalog, never trusted from
    the caller.
    """

    business_config_id: str
    order_id: str
    line_id: str
    external_message_id: str
    conversation_id: Optional[str] = None
    quantity: Optional[int] = None
    modifier_option_ids: Optional[List[str]] = None
    removed_ingredient_ids: Optional[List[str]] = None


@dataclass
class UpdateItemInOrderResponse:
    order_id: str
    line_id: str
    total_amount: str
    line_count: int
    version: int
    replayed: bool = False
    superseded_attempt_ids: Tuple[str, ...] = ()


class UpdateItemInOrderPort(ABC):
    @abstractmethod
    def execute(self, command: UpdateItemInOrderCommand) -> UpdateItemInOrderResponse:
        pass
