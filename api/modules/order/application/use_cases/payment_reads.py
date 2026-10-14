"""Read payment attempts for the panel: list (with filters) and detail."""
from __future__ import annotations

from typing import Optional

from modules.order.application.ports.driven.payment_repository import (
    PaymentAttemptRepository,
)
from modules.order.application.ports.driver.payment_reads_ports import (
    GetPaymentPort,
    ListPaymentsPort,
    ListPaymentsQuery,
)
from modules.order.domain.models.payment_attempt import PaymentAttempt
from modules.order.domain.models.payment_status import PaymentStatus


class ListPaymentsUseCase(ListPaymentsPort):
    def __init__(self, payment_repo: PaymentAttemptRepository) -> None:
        self._payment_repo = payment_repo

    def execute(self, query: ListPaymentsQuery) -> list[PaymentAttempt]:
        status: Optional[PaymentStatus] = None
        if query.status:
            try:
                status = PaymentStatus(query.status)
            except ValueError:
                status = None
        return self._payment_repo.list_all(status=status, provider=query.provider or None)


class GetPaymentUseCase(GetPaymentPort):
    def __init__(self, payment_repo: PaymentAttemptRepository) -> None:
        self._payment_repo = payment_repo

    def execute(self, payment_id: str) -> Optional[PaymentAttempt]:
        return self._payment_repo.get_by_id(payment_id)
