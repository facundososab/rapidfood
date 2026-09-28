from abc import ABC, abstractmethod
from dataclasses import dataclass
from typing import Optional


@dataclass
class CreatePaymentCheckoutCommand:
    order_id: str


@dataclass
class CreatePaymentCheckoutResult:
    order_id: str
    payment_attempt_id: str
    provider: str
    checkout_url: str
    status: str
    order_version: int
    created: bool


@dataclass
class HandlePaymentWebhookCommand:
    provider: str
    data_id: str
    topic: str
    raw_payload: dict
    headers: dict


@dataclass
class HandlePaymentWebhookResult:
    payment_attempt_id: Optional[str]
    status: str
    order_id: Optional[str]
    order_status: Optional[str]
    processed: bool
    applied: bool


@dataclass
class CancelSupersededCheckoutCommand:
    payment_attempt_id: str


@dataclass
class CancelSupersededCheckoutResult:
    payment_attempt_id: str
    cancellation_status: str
    already_cancelled: bool


class CreatePaymentCheckoutPort(ABC):
    @abstractmethod
    def execute(
        self, command: CreatePaymentCheckoutCommand
    ) -> CreatePaymentCheckoutResult:
        pass


class HandlePaymentWebhookPort(ABC):
    @abstractmethod
    def execute(
        self, command: HandlePaymentWebhookCommand
    ) -> HandlePaymentWebhookResult:
        pass


class CancelSupersededCheckoutPort(ABC):
    @abstractmethod
    def execute(
        self, command: CancelSupersededCheckoutCommand
    ) -> CancelSupersededCheckoutResult:
        pass
