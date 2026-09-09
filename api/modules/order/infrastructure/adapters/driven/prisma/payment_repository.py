from __future__ import annotations

from decimal import Decimal
from uuid import uuid4

from prisma import Prisma

from modules.order.application.ports.driven.payment_repository import PaymentRepository
from modules.order.domain.models.payment import Payment
from modules.order.domain.models.payment_status import PaymentStatus
from modules.order.infrastructure.adapters.driven.prisma.mappers.payment_mapper import (
    payment_to_domain,
    payment_to_prisma_data,
)


class PrismaPaymentRepository(PaymentRepository):
    def __init__(self, prisma_client: Prisma) -> None:
        self._prisma = prisma_client

    def create_pending(
        self,
        order_id: str,
        provider: str,
        amount: Decimal,
        external_reference: str,
    ) -> Payment:
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
        return payment_to_domain(row)

    def save(self, payment: Payment) -> Payment:
        row = self._prisma.payment.update(
            where={"id": payment.id},
            data=payment_to_prisma_data(payment),
        )
        return payment_to_domain(row)

    def get_by_external_id(self, external_id: str) -> Payment | None:
        row = self._prisma.payment.find_first(where={"externalId": external_id})
        return payment_to_domain(row) if row is not None else None

    def get_by_preference_id(self, preference_id: str) -> Payment | None:
        row = self._prisma.payment.find_first(where={"preferenceId": preference_id})
        return payment_to_domain(row) if row is not None else None

    def get_by_external_reference(self, external_reference: str) -> Payment | None:
        row = self._prisma.payment.find_first(
            where={"externalReference": external_reference},
            order={"createdAt": "desc"},
        )
        return payment_to_domain(row) if row is not None else None

    def update_status(self, payment_id: str, status: PaymentStatus) -> Payment:
        row = self._prisma.payment.update(
            where={"id": payment_id},
            data={"status": status.value},
        )
        return payment_to_domain(row)
