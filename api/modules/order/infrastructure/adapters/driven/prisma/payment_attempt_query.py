"""Prisma adapter for payment-attempt modification queries.

Works with either the base client or a transaction client (the executor passes
the tx-bound instance), so superseding an attempt lands in the same transaction
as the order mutation.
"""
from __future__ import annotations

from datetime import datetime
from decimal import Decimal
from typing import Any, Optional

from modules.order.application.ports.driven.payment_attempt_query import (
    PaymentAttemptQueryPort,
    PaymentAttemptView,
)
from modules.order.domain.models.payment_status import PaymentStatus

_APPROVED = PaymentStatus.APPROVED.value
_CANCELLATION_PENDING = "PENDING"


class PrismaPaymentAttemptQuery(PaymentAttemptQueryPort):
    def __init__(self, client: Any) -> None:
        self._client = client

    def has_current_approved(self, order_id: str, version: int) -> bool:
        row = self._client.payment.find_first(
            where={
                "orderId": order_id,
                "orderVersion": version,
                "status": _APPROVED,
                "supersededAt": None,
            }
        )
        return row is not None

    def current_for_version(
        self, order_id: str, version: int
    ) -> Optional[PaymentAttemptView]:
        row = self._client.payment.find_first(
            where={
                "orderId": order_id,
                "orderVersion": version,
                "supersededAt": None,
            },
            order={"createdAt": "desc"},
        )
        if row is None:
            return None
        return _to_view(row)

    def supersede_current(self, order_id: str, version: int, at: datetime) -> list[str]:
        rows = self._client.payment.find_many(
            where={
                "orderId": order_id,
                "orderVersion": version,
                "supersededAt": None,
            }
        )
        ids = [row.id for row in rows]
        if ids:
            # Marked for a best-effort remote cancellation after the commit.
            self._client.payment.update_many(
                data={
                    "supersededAt": at,
                    "cancellationStatus": _CANCELLATION_PENDING,
                },
                where={"id": {"in": ids}},
            )
        return ids


def _to_view(row) -> PaymentAttemptView:
    return PaymentAttemptView(
        id=row.id,
        order_id=row.orderId,
        order_version=row.orderVersion,
        status=_enum_value(row.status),
        superseded=row.supersededAt is not None,
        amount=Decimal(str(row.amount)),
        provider=row.provider,
        external_id=row.externalId,
        checkout_url=row.checkoutUrl,
        cancellation_status=row.cancellationStatus,
    )


def _enum_value(value) -> str:
    return value.value if hasattr(value, "value") else str(value)
