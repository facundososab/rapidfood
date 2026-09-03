"""Coupon code value object (pure domain).

Normalizes coupon codes to uppercase and validates the format. Codes are
alphanumeric strings (A-Z, 0-9); whitespace is stripped before normalization.
"""

from __future__ import annotations

import re
from dataclasses import dataclass

from modules.config_coupon.domain.errors.coupon_errors import (
    CouponCodeRequiredError,
    InvalidCouponCodeError,
)

_COUPON_CODE_PATTERN = re.compile(r"^[A-Z0-9]+$")


@dataclass(frozen=True, slots=True)
class CouponCode:
    """Immutable normalized coupon code.

    Raises:
        CouponCodeRequiredError: if the code is empty after stripping.
        InvalidCouponCodeError: if the code contains invalid characters.
    """

    value: str

    def __post_init__(self) -> None:
        normalized = self.value.strip().upper()
        if not normalized:
            raise CouponCodeRequiredError("Coupon code must not be empty")
        if not _COUPON_CODE_PATTERN.match(normalized):
            raise InvalidCouponCodeError(
                f"Coupon code '{self.value}' must contain only letters and digits"
            )
        object.__setattr__(self, "value", normalized)