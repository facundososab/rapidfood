"""Driven port: the payment provider (Mercado Pago Checkout Pro).

Two DIFFERENT operations with INDEPENDENT idempotency keys:
  - ``create_checkout`` creates a checkout for one logical attempt;
  - ``cancel_checkout`` cancels a superseded checkout.

Stable keys matter: if the provider creates the resource but the response is
lost to a timeout, the retry MUST reuse the same key so a second checkout is not
created. ``run_id``-style tracing identifiers never participate.
"""
from abc import ABC, abstractmethod
from dataclasses import dataclass, field
from decimal import Decimal
from typing import Optional

from modules.order.domain.models.payment_status import PaymentStatus


class PaymentProviderError(Exception):
    """Technical failure talking to the payment provider (timeout, 5xx, ...).

    Distinct from a business outcome: an unavailable provider is NOT "the
    address is outside the zone" and must not be presented as a business result.
    """
    pass


@dataclass(frozen=True)
class CreateCheckoutRequest:
    order_id: str
    attempt_id: str
    amount: Decimal
    currency: str
    external_reference: str
    idempotency_key: str
    description: Optional[str] = None
    notification_url: Optional[str] = None
    back_urls: dict = field(default_factory=dict)


@dataclass(frozen=True)
class CreateCheckoutResult:
    external_id: str
    checkout_url: str
    external_reference: str


@dataclass(frozen=True)
class CancelCheckoutRequest:
    external_id: str
    idempotency_key: str


@dataclass(frozen=True)
class CancelCheckoutResult:
    already_cancelled: bool = False


@dataclass(frozen=True)
class ProviderPayment:
    external_id: str
    status: PaymentStatus
    external_reference: Optional[str] = None
    amount: Optional[Decimal] = None


class PaymentProviderPort(ABC):
    @abstractmethod
    def create_checkout(self, request: CreateCheckoutRequest) -> CreateCheckoutResult:
        pass

    @abstractmethod
    def cancel_checkout(self, request: CancelCheckoutRequest) -> CancelCheckoutResult:
        pass

    @abstractmethod
    def get_payment(self, external_id: str) -> Optional[ProviderPayment]:
        """Fetch the authoritative provider state, or None when it is unknown.

        None means "the provider does not know this id" (a non-retryable, benign
        case, e.g. a simulated/unknown notification); a transient failure raises
        PaymentProviderError so the caller can ask the provider to retry.
        """
        pass
