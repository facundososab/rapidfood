from abc import ABC, abstractmethod
from dataclasses import dataclass
from decimal import Decimal
from typing import Optional

from modules.order.domain.models.payment_status import PaymentStatus


@dataclass
class CreateCheckoutLinkRequest:
    order_id: str
    payment_id: str
    amount: Decimal
    currency: str
    external_reference: str


@dataclass
class CreateCheckoutLinkResult:
    preference_id: str
    checkout_url: str
    external_reference: str
    external_id: Optional[str] = None


@dataclass
class ProviderPayment:
    external_id: str
    status: PaymentStatus
    external_reference: Optional[str] = None
    preference_id: Optional[str] = None
    amount: Optional[Decimal] = None


class PaymentProvider(ABC):
    @abstractmethod
    def create_checkout_link(
        self, request: CreateCheckoutLinkRequest
    ) -> CreateCheckoutLinkResult:
        pass

    @abstractmethod
    def get_payment(self, external_id: str) -> ProviderPayment:
        pass
