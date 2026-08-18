from abc import ABC, abstractmethod
from dataclasses import dataclass


@dataclass
class RemoveLineCommand:
    order_id: str
    product_id: str


@dataclass
class RemoveLineResponse:
    order_id: str
    total_amount: str
    line_count: int


class RemoveLinePort(ABC):
    @abstractmethod
    def remove_line(self, command: RemoveLineCommand) -> RemoveLineResponse:
        pass
