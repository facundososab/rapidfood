from abc import ABC, abstractmethod
from dataclasses import dataclass


@dataclass
class UpdateOrderStatusCommand:
    order_id: str
    status: str


@dataclass
class UpdateOrderStatusResponse:
    order_id: str
    status: str


class UpdateOrderStatusPort(ABC):
    @abstractmethod
    def execute(self, command: UpdateOrderStatusCommand) -> UpdateOrderStatusResponse:
        pass