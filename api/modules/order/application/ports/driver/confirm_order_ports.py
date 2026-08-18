from abc import ABC, abstractmethod
from dataclasses import dataclass


@dataclass
class ConfirmOrderCommand:
    order_id: str


@dataclass
class ConfirmOrderResponse:
    order_id: str
    status: str
    confirmed_at: str


class ConfirmOrderPort(ABC):
    @abstractmethod
    def execute(self, command: ConfirmOrderCommand) -> ConfirmOrderResponse:
        pass
