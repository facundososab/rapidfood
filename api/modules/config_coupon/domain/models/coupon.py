"""Coupon aggregate root (pure domain).

Encapsulates all coupon business rules agreed with the business owner:

- ``FIXED_AMOUNT`` coupons require a minimum order amount (RN interview Q1)
  and can never discount more than the subtotal (total never goes negative).
- ``PERCENTAGE`` coupons have NO discount cap (Q1).
- ``available_uses`` is a GLOBAL counter (Q2); per-client limits are a future
  refinement. Uses are consumed when the order leaves BORRADOR -> PENDIENTE,
  NOT when the coupon is merely applied to a draft (Q2).
- Coupons expire at the END of the day (23:59:59) of ``date_of_expiration`` (Q4).
- ``is_active`` is an explicit pause/activate flag (Q4).
- One coupon per order and "discount applies to subtotal, shipping added
  afterwards" are ORDER-context rules (Q3) enforced by the order module, not
  here — this entity only validates/calculates against a subtotal.
"""

from __future__ import annotations

from dataclasses import dataclass
from datetime import datetime
from decimal import ROUND_HALF_UP, Decimal

from modules.config_coupon.domain.errors.coupon_errors import (
    CouponDepletedError,
    CouponExpiredError,
    CouponInactiveError,
    InvalidCouponAmountError,
    InvalidCouponUsesError,
    CouponMinOrderNotReachedError,
)
from modules.config_coupon.domain.models.coupon_code import CouponCode
from modules.config_coupon.domain.models.coupon_type import CouponType

_DECIMAL_ZERO = Decimal("0")
_DECIMAL_100 = Decimal("100")
_MONEY_QUANTUM = Decimal("0.01")


@dataclass(slots=True)
class Coupon:
    """A discount coupon configured by the business admin.

    Attributes:
        coupon_id: optional persistence id (None until saved).
        coupon_code: normalized unique code.
        coupon_type: FIXED_AMOUNT or PERCENTAGE.
        amount: fixed amount or percentage value.
        min_order_amount: required subtotal minimum for FIXED_AMOUNT coupons.
        available_uses: remaining GLOBAL uses (counter).
        date_of_expiration: last day the coupon is valid (end of that day).
        is_active: administrative pause flag.
    """

    coupon_code: CouponCode
    coupon_type: CouponType
    amount: Decimal
    available_uses: int
    min_order_amount: Decimal | None = None
    date_of_expiration: datetime | None = None
    is_active: bool = True
    coupon_id: str | None = None

    def __post_init__(self) -> None:
        if self.amount <= _DECIMAL_ZERO:
            raise InvalidCouponAmountError("Coupon amount must be greater than zero")
        if self.coupon_type is CouponType.PERCENTAGE and self.amount > _DECIMAL_100:
            raise InvalidCouponAmountError("Percentage coupon amount cannot exceed 100")
        if self.coupon_type is CouponType.FIXED_AMOUNT:
            if self.min_order_amount is None:
                raise InvalidCouponAmountError(
                    "Fixed-amount coupon requires a minimum order amount"
                )
            if self.min_order_amount < _DECIMAL_ZERO:
                raise InvalidCouponAmountError(
                    "Minimum order amount cannot be negative"
                )
        if self.available_uses < 0:
            raise InvalidCouponUsesError("Available uses cannot be negative")

    @property
    def is_fixed_amount(self) -> bool:
        return self.coupon_type is CouponType.FIXED_AMOUNT

    @property
    def is_percentage(self) -> bool:
        return self.coupon_type is CouponType.PERCENTAGE

    def is_expired(self, current_datetime: datetime) -> bool:
        """True if ``current_datetime`` is past the coupon's last valid day.

        Expiration is at the END of ``date_of_expiration`` (23:59:59): the
        coupon is still valid for the whole of that calendar day.
        """
        if self.date_of_expiration is None:
            return False
        return current_datetime.date() > self.date_of_expiration.date()

    def validate_applicable(
        self,
        subtotal: Decimal,
        current_datetime: datetime,
    ) -> None:
        """Validate the coupon against an order subtotal.

        Raises the FIRST violated rule:
        1. inactive (paused)
        2. depleted (no global uses left)
        3. expired (past end of expiration day)
        4. fixed-amount minimum order not reached
        """
        if not self.is_active:
            raise CouponInactiveError(self.coupon_code.value)
        if self.available_uses <= 0:
            raise CouponDepletedError(self.coupon_code.value)
        if self.is_expired(current_datetime):
            raise CouponExpiredError(self.coupon_code.value)
        if self.is_fixed_amount:
            if self.min_order_amount is not None and subtotal < self.min_order_amount:
                raise CouponMinOrderNotReachedError(self.coupon_code.value)

    def calculate_discount(self, subtotal: Decimal) -> Decimal:
        """Compute the discount for a subtotal (assumes coupon is applicable).

        - FIXED_AMOUNT: min(amount, subtotal) — never discounts more than the
          order subtotal.
        - PERCENTAGE: subtotal * amount / 100 — no cap.

        Amounts are rounded half-up to 2 decimals.
        """
        if subtotal < _DECIMAL_ZERO:
            raise InvalidCouponAmountError("Subtotal cannot be negative")
        if self.is_percentage:
            discount = subtotal * self.amount / _DECIMAL_100
        else:
            discount = min(self.amount, subtotal)
        return discount.quantize(_MONEY_QUANTUM, rounding=ROUND_HALF_UP)

    def validate_consumable(self, current_datetime: datetime) -> None:
        """Validate the coupon can still be CONSUMED at confirmation time.

        Checks active, not expired, and remaining uses. The min-order check is
        NOT repeated here: it was validated against the real subtotal at draft
        time (ValidateCouponUseCase) and the discount is frozen in the order's
        applied_coupon snapshot (RN-033/034).
        """
        if not self.is_active:
            raise CouponInactiveError(self.coupon_code.value)
        if self.available_uses <= 0:
            raise CouponDepletedError(self.coupon_code.value)
        if self.is_expired(current_datetime):
            raise CouponExpiredError(self.coupon_code.value)

    def consume_use(self) -> None:
        """Decrement the global use counter (called on BORRADOR -> PENDIENTE)."""
        if self.available_uses <= 0:
            raise CouponDepletedError(self.coupon_code.value)
        self.available_uses -= 1

    def pause(self) -> None:
        """Administratively disable the coupon."""
        self.is_active = False

    def activate(self) -> None:
        """Administratively re-enable the coupon."""
        self.is_active = True