"""Driver ports: read payment attempts for the panel (list + detail)."""
from __future__ import annotations

from abc import ABC, abstractmethod
from dataclasses import dataclass
from typing import Optional

from modules.order.domain.models.payment_attempt import PaymentAttempt


@dataclass(frozen=True)
class ListPaymentsQuery:
    status: Optional[str] = None
    provider: Optional[str] = None


class ListPaymentsPort(ABC):
    @abstractmethod
    def execute(self, query: ListPaymentsQuery) -> list[PaymentAttempt]:
        ...


class GetPaymentPort(ABC):
    @abstractmethod
    def execute(self, payment_id: str) -> Optional[PaymentAttempt]:
        ...
