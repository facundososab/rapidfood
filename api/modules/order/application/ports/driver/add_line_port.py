from abc import ABC, abstractmethod
from dataclasses import dataclass, field
from typing import List


@dataclass
class AddLineCommand:
    order_id: str
    product_variant_id: str
    quantity: int
    modifier_option_ids: List[str] = field(default_factory=list)
    removed_ingredient_ids: List[str] = field(default_factory=list)


@dataclass
class AddLineResponse:
    order_id: str
    line_id: str
    total_amount: str
    line_count: int


class AddLinePort(ABC):
    @abstractmethod
    def add_line(self, command: AddLineCommand) -> AddLineResponse:
        pass
