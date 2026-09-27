from __future__ import annotations

from decimal import Decimal
from typing import Optional
from uuid import uuid4

from prisma import Prisma

from modules.order.application.ports.driven.payment_repository import (
    PaymentAttemptRepository,
)
from modules.order.domain.models.payment_attempt import PaymentAttempt
from modules.order.domain.models.payment_status import PaymentStatus
from modules.order.infrastructure.adapters.driven.prisma.mappers.payment_attempt_mapper import (
    payment_attempt_to_domain,
    payment_attempt_to_prisma_data,
)


class PrismaPaymentRepository(PaymentAttemptRepository):
    def __init__(self, prisma_client: Prisma) -> None:
        self._prisma = prisma_client

    def create_pending(
        self,
        order_id: str,
        provider: str,
        amount: Decimal,
        external_reference: str,
    ) -> PaymentAttempt:
        row = self._prisma.payment.create(
            {
                "id": str(uuid4()),
                "orderId": order_id,
                "provider": provider,
                "amount": amount,
                "status": PaymentStatus.PENDING.value,
                "externalReference": external_reference,
            }
        )
        return payment_attempt_to_domain(row)

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
        row = self._prisma.payment.create(
            {
                "id": attempt_id or str(uuid4()),
                "orderId": order_id,
                "provider": provider,
                "amount": amount,
                "status": PaymentStatus.PENDING.value,
                "orderVersion": order_version,
                "externalReference": external_reference,
                "createIdempotencyKey": create_idempotency_key,
            }
        )
        return payment_attempt_to_domain(row)

    def save(self, attempt: PaymentAttempt) -> PaymentAttempt:
        row = self._prisma.payment.update(
            where={"id": attempt.id},
            data=payment_attempt_to_prisma_data(attempt),
        )
        return payment_attempt_to_domain(row)

    def get_by_id(self, payment_attempt_id: str) -> Optional[PaymentAttempt]:
        row = self._prisma.payment.find_unique(where={"id": payment_attempt_id})
        return payment_attempt_to_domain(row) if row is not None else None

    def get_by_external_id(self, external_id: str) -> Optional[PaymentAttempt]:
        row = self._prisma.payment.find_first(where={"externalId": external_id})
        return payment_attempt_to_domain(row) if row is not None else None

    def get_by_preference_id(self, preference_id: str) -> Optional[PaymentAttempt]:
        row = self._prisma.payment.find_first(where={"preferenceId": preference_id})
        return payment_attempt_to_domain(row) if row is not None else None

    def get_by_external_reference(self, external_reference: str) -> Optional[PaymentAttempt]:
        row = self._prisma.payment.find_first(
            where={"externalReference": external_reference},
            order={"createdAt": "desc"},
        )
        return payment_attempt_to_domain(row) if row is not None else None

    def find_current_for_version(
        self, order_id: str, version: int
    ) -> Optional[PaymentAttempt]:
        row = self._prisma.payment.find_first(
            where={
                "orderId": order_id,
                "orderVersion": version,
                "supersededAt": None,
            },
            order={"createdAt": "desc"},
        )
        return payment_attempt_to_domain(row) if row is not None else None

    def update_status(self, payment_id: str, status: PaymentStatus) -> PaymentAttempt:
        row = self._prisma.payment.update(
            where={"id": payment_id},
            data={"status": status.value},
        )
        return payment_attempt_to_domain(row)
