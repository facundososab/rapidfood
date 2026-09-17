from abc import ABC, abstractmethod
from datetime import datetime
from decimal import Decimal
from typing import Optional

from modules.order.domain.models.payment_attempt import PaymentAttempt
from modules.order.domain.models.payment_status import PaymentStatus


class PaymentAttemptRepository(ABC):
    """Persistence for payment attempts bound to an order version."""

    @abstractmethod
    def create_pending(
        self,
        order_id: str,
        provider: str,
        amount: Decimal,
        external_reference: str,
    ) -> PaymentAttempt:
        pass

    @abstractmethod
    def create_for_version(
        self,
        *,
        order_id: str,
        provider: str,
        amount: Decimal,
        order_version: int,
        external_reference: str,
        create_idempotency_key: str,
        attempt_id: Optional[str] = None,
    ) -> PaymentAttempt:
        """Reserve the single logical attempt for this order version.

        Persisted BEFORE the remote call so a timeout retry can reuse the same
        provider idempotency key instead of creating a second checkout.
        """
        pass

    @abstractmethod
    def save(self, attempt: PaymentAttempt) -> PaymentAttempt:
        pass

    @abstractmethod
    def get_by_id(self, payment_attempt_id: str) -> Optional[PaymentAttempt]:
        pass

    @abstractmethod
    def get_by_external_id(self, external_id: str) -> Optional[PaymentAttempt]:
        pass

    @abstractmethod
    def get_by_preference_id(self, preference_id: str) -> Optional[PaymentAttempt]:
        pass

    @abstractmethod
    def get_by_external_reference(self, external_reference: str) -> Optional[PaymentAttempt]:
        pass

    @abstractmethod
    def find_current_for_version(
        self, order_id: str, version: int
    ) -> Optional[PaymentAttempt]:
        """The live (non-superseded) attempt for an order version, if any."""
        pass

    @abstractmethod
    def update_status(self, payment_id: str, status: PaymentStatus) -> PaymentAttempt:
        pass
