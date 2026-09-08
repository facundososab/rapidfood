from abc import ABC, abstractmethod
from dataclasses import dataclass


@dataclass
class CreatePaymentLinkCommand:
    order_id: str


@dataclass
class CreatePaymentLinkResult:
    order_id: str
    payment_id: str
    provider: str
    checkout_url: str
    status: str


@dataclass
class ProcessPaymentNotificationCommand:
    provider: str
    data_id: str
    topic: str
    raw_payload: dict
    headers: dict


@dataclass
class ProcessPaymentNotificationResult:
    payment_id: str
    status: str
    order_id: str
    order_status: str
    processed: bool


class CreatePaymentLinkPort(ABC):
    @abstractmethod
    def execute(self, command: CreatePaymentLinkCommand) -> CreatePaymentLinkResult:
        pass


class ProcessPaymentNotificationPort(ABC):
    @abstractmethod
    def execute(
        self, command: ProcessPaymentNotificationCommand
    ) -> ProcessPaymentNotificationResult:
        pass
