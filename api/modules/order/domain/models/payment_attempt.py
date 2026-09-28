"""Payment attempt for an Order.

Each row is an immutable-in-spirit attempt bound to an ``Order.version``: it
records the provider status AND its local validity, which are separate concepts.
A stale attempt can be ``providerStatus = APPROVED`` and ``supersededAt`` set at
the same time (a race where an old checkout still got paid); it is then kept for
refund/reconciliation but must never pay the current order version.
"""
from __future__ import annotations

from dataclasses import dataclass
from datetime import datetime
from decimal import Decimal
from typing import Optional

from modules.order.domain.models.cancellation_status import CancellationStatus
from modules.order.domain.models.payment_status import PaymentStatus


@dataclass
class PaymentAttempt:
    id: str
    order_id: str
    provider: str
    amount: Decimal
    status: PaymentStatus
    order_version: Optional[int] = None
    external_id: Optional[str] = None
    preference_id: Optional[str] = None
    checkout_url: Optional[str] = None
    external_reference: Optional[str] = None
    expires_at: Optional[datetime] = None
    superseded_at: Optional[datetime] = None
    cancellation_status: Optional[CancellationStatus] = None
    create_idempotency_key: Optional[str] = None
    cancel_idempotency_key: Optional[str] = None

    @property
    def superseded(self) -> bool:
        return self.superseded_at is not None

    def is_approved(self) -> bool:
        return self.status is PaymentStatus.APPROVED

    def is_current_for(self, version: int) -> bool:
        """Bound to the given order version and not superseded."""
        return not self.superseded and self.order_version == version

    def has_same_final_status(self, status: PaymentStatus) -> bool:
        return self.status == status and status.is_final()

    def mark_checkout_created(
        self,
        *,
        external_id: str,
        checkout_url: str,
        external_reference: Optional[str] = None,
    ) -> None:
        self.external_id = external_id
        self.checkout_url = checkout_url
        if external_reference is not None:
            self.external_reference = external_reference

    def update_provider_status(self, status: PaymentStatus) -> None:
        self.status = status

    def supersede(self, at: datetime) -> None:
        """Mark the attempt obsolete locally (independent from its status)."""
        if self.superseded_at is None:
            self.superseded_at = at
        if self.cancellation_status is None:
            self.cancellation_status = CancellationStatus.PENDING

    def mark_remote_cancelled(self) -> None:
        self.cancellation_status = CancellationStatus.CANCELLED

    def mark_remote_already_cancelled(self) -> None:
        self.cancellation_status = CancellationStatus.REMOTE_ALREADY_CANCELLED

    def mark_cancellation_failed(self) -> None:
        self.cancellation_status = CancellationStatus.FAILED
