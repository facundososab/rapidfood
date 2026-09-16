from abc import ABC, abstractmethod
from decimal import Decimal
from typing import Optional

from modules.order.domain.models.payment import Payment
from modules.order.domain.models.payment_status import PaymentStatus


class PaymentRepository(ABC):
    @abstractmethod
    def create_pending(
        self,
        order_id: str,
        provider: str,
        amount: Decimal,
        external_reference: str,
    ) -> Payment:
        pass

    @abstractmethod
    def save(self, payment: Payment) -> Payment:
        pass

    @abstractmethod
    def get_by_external_id(self, external_id: str) -> Optional[Payment]:
        pass

    @abstractmethod
    def get_by_preference_id(self, preference_id: str) -> Optional[Payment]:
        pass

    @abstractmethod
    def get_by_external_reference(self, external_reference: str) -> Optional[Payment]:
        pass

    @abstractmethod
    def update_status(self, payment_id: str, status: PaymentStatus) -> Payment:
        pass
