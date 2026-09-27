"""Driven port: read/supersede payment attempts for order modification.

Modification readiness depends on whether an attempt for the order's CURRENT
version was approved. This is a persistence concern owned by the venue; the
application only reads the answer and marks the old attempt superseded.

The concrete adapter is transaction-aware: the executor passes the tx-bound
instance so the supersede lands in the same transaction as the mutation.
"""
from __future__ import annotations

from dataclasses import dataclass
from datetime import datetime
from decimal import Decimal
from typing import Optional, Protocol


@dataclass(frozen=True, slots=True)
class PaymentAttemptView:
    id: str
    order_id: str
    order_version: Optional[int]
    status: str
    superseded: bool
    amount: Decimal
    provider: str
    external_id: Optional[str] = None
    checkout_url: Optional[str] = None
    cancellation_status: Optional[str] = None


class PaymentAttemptQueryPort(Protocol):
    def has_current_approved(self, order_id: str, version: int) -> bool:
        """True when an approved, non-superseded attempt exists for this version."""
        ...

    def current_for_version(self, order_id: str, version: int) -> Optional[PaymentAttemptView]:
        """The live (non-superseded) attempt for a version, if any."""
        ...

    def supersede_current(self, order_id: str, version: int, at: datetime) -> list[str]:
        """Mark every live attempt for the version superseded. Returns their ids.

        The ids are returned so the caller can attempt remote cancellation after
        the local transaction commits.
        """
        ...
