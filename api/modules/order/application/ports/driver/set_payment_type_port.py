from abc import ABC, abstractmethod
from dataclasses import dataclass


@dataclass
class SetPaymentTypeCommand:
    order_id: str
    payment_type: str


@dataclass
class SetPaymentTypeResponse:
    order_id: str
    payment_type: str


class SetPaymentTypePort(ABC):
    @abstractmethod
    def execute(self, command: SetPaymentTypeCommand) -> SetPaymentTypeResponse:
        pass
