from abc import ABC, abstractmethod
from dataclasses import dataclass


@dataclass
class UpdateLineQuantityCommand:
    order_id: str
    line_id: str
    quantity: int


@dataclass
class UpdateLineQuantityResponse:
    order_id: str
    total_amount: str
    line_count: int


class UpdateLineQuantityPort(ABC):
    @abstractmethod
    def update_line_quantity(self, command: UpdateLineQuantityCommand) -> UpdateLineQuantityResponse:
        pass
