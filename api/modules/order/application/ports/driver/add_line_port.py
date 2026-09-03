from abc import ABC, abstractmethod
from dataclasses import dataclass


@dataclass
class AddLineCommand:
    order_id: str
    product_id: str
    quantity: int


@dataclass
class AddLineResponse:
    order_id: str
    total_amount: str
    line_count: int


class AddLinePort(ABC):
    @abstractmethod
    def add_line(self, command: AddLineCommand) -> AddLineResponse:
        pass
