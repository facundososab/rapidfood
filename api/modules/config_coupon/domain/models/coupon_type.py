"""Coupon type enumeration (pure domain)."""

from __future__ import annotations

from enum import Enum

from modules.config_coupon.domain.errors.coupon_errors import InvalidCouponTypeError


class CouponType(str, Enum):
    """Supported coupon discount types.

    - ``FIXED_AMOUNT``: discounts a fixed amount, requires a minimum order
      amount (``min_order_amount``) and cannot exceed the order subtotal.
    - ``PERCENTAGE``: discounts a percentage of the subtotal, no cap.
    """

    FIXED_AMOUNT = "FIXED_AMOUNT"
    PERCENTAGE = "PERCENTAGE"

    @classmethod
    def from_value(cls, value: str) -> "CouponType":
        """Build from a raw string, raising a domain error on unknown types."""
        normalized = value.strip().upper()
        try:
            return cls(normalized)
        except ValueError:
            raise InvalidCouponTypeError(value) from None