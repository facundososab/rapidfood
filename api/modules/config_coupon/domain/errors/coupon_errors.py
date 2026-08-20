"""Domain errors for the coupon bounded context.

These are pure-Python business errors. They are NEVER HTTP exceptions —
the REST inbound adapter is responsible for translating them to HTTP codes.
"""

from __future__ import annotations


class DomainError(Exception):
    """Base class for all coupon domain errors."""


class InvalidCouponCodeError(DomainError):
    """Coupon code is empty or has an invalid format."""


class InvalidCouponAmountError(DomainError):
    """Coupon amount is not valid for its type (e.g. negative/out-of-range)."""


class InvalidCouponUsesError(DomainError):
    """Coupon available uses is negative."""


class CouponCodeRequiredError(DomainError):
    """A coupon code value object was built without a code."""


class CouponNotFoundError(DomainError):
    """No coupon exists for the given code/id."""

    def __init__(self, value: str) -> None:
        super().__init__(f"Coupon not found: {value}")
        self.value = value


class CouponInactiveError(DomainError):
    """The coupon exists but was paused/disabled (is_active flag)."""

    def __init__(self, coupon_code: str) -> None:
        super().__init__(f"Coupon is inactive: {coupon_code}")


class CouponExpiredError(DomainError):
    """The coupon is past its expiration date (end of day)."""

    def __init__(self, coupon_code: str) -> None:
        super().__init__(f"Coupon is expired: {coupon_code}")


class CouponDepletedError(DomainError):
    """The coupon has no remaining uses available."""

    def __init__(self, coupon_code: str) -> None:
        super().__init__(f"Coupon has no remaining uses: {coupon_code}")


class CouponMinOrderNotReachedError(DomainError):
    """Fixed-amount coupon requires a minimum subtotal that is not met."""

    def __init__(self, coupon_code: str) -> None:
        super().__init__(f"Coupon minimum order not reached: {coupon_code}")


class CouponCannotApplyError(DomainError):
    """Generic: the coupon cannot be applied to the given order subtotal."""


class InvalidCouponTypeError(DomainError):
    """Coupon type is not a supported value (FIXED_AMOUNT | PERCENTAGE)."""

    def __init__(self, value: str) -> None:
        super().__init__(f"Invalid coupon type: {value}")


class CouponAlreadyExistsError(DomainError):
    """A coupon with the same code already exists (coupon_code is unique)."""

    def __init__(self, coupon_code: str) -> None:
        super().__init__(f"Coupon already exists: {coupon_code}")