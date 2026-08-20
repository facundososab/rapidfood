"""Coupon application driver ports — operations exposed to the ORDER module.

These are the cross-module contracts. The order module consumes these ports
(never the coupon adapters/use_cases/domain directly) to:

- validate a coupon against a draft subtotal and get the discount (REQ-020,
  RN-033/034) — BEFORE confirming, while the order is BORRADOR.
- consume one global use when the order leaves BORRADOR -> PENDIENTE (Q2).

The response carries the full coupon snapshot (code, type, amount,
discount_amount, available_uses, date_of_expiration) so the order module can
freeze it into its ``applied_coupon`` record (RN-033/034).
"""

from __future__ import annotations

from dataclasses import dataclass
from datetime import datetime
from decimal import Decimal
from typing import Protocol


@dataclass(frozen=True, slots=True)
class ValidateCouponCommand:
    """Validate a coupon code against an order subtotal (BORRADOR state).

    Attributes:
        coupon_code: coupon code to validate.
        subtotal: current order subtotal (sum of line amounts).
    """

    coupon_code: str
    subtotal: Decimal


@dataclass(frozen=True, slots=True)
class ValidateCouponResponse:
    """Result of validating a coupon against a subtotal.

    ``discount_amount`` is the exact discount to freeze into the order's
    applied_coupon snapshot (RN-033/034).
    """

    coupon_id: str
    coupon_code: str
    coupon_type: str
    amount: Decimal
    discount_amount: Decimal
    available_uses: int
    date_of_expiration: datetime | None


class ValidateCouponPort(Protocol):
    def execute(self, command: ValidateCouponCommand) -> ValidateCouponResponse: ...


@dataclass(frozen=True, slots=True)
class ConsumeCouponCommand:
    """Consume one global use of a coupon (BORRADOR -> PENDIENTE).

    Attributes:
        coupon_code: coupon code whose use counter is decremented.
    """

    coupon_code: str


@dataclass(frozen=True, slots=True)
class ConsumeCouponResponse:
    coupon_code: str
    remaining_uses: int


class ConsumeCouponPort(Protocol):
    def execute(self, command: ConsumeCouponCommand) -> ConsumeCouponResponse: ...