"""Tests for the CouponCode value object."""

from __future__ import annotations

from decimal import Decimal

import pytest

from modules.config_coupon.domain.errors.coupon_errors import (
    CouponCodeRequiredError,
    InvalidCouponCodeError,
)
from modules.config_coupon.domain.models.coupon import Coupon
from modules.config_coupon.domain.models.coupon_code import CouponCode
from modules.config_coupon.domain.models.coupon_type import CouponType


class TestCouponCodeNormalization:
    def test_uppercases_code(self) -> None:
        assert CouponCode("bienvenida10").value == "BIENVENIDA10"

    def test_strips_whitespace(self) -> None:
        assert CouponCode("  code10  ").value == "CODE10"

    def test_keeps_already_normalized(self) -> None:
        assert CouponCode("BIENVENIDA10").value == "BIENVENIDA10"

    def test_accepts_digits_and_letters(self) -> None:
        assert CouponCode("A1B2C3").value == "A1B2C3"


class TestCouponCodeValidation:
    def test_rejects_empty(self) -> None:
        with pytest.raises(CouponCodeRequiredError):
            CouponCode("   ")

    def test_rejects_special_characters(self) -> None:
        with pytest.raises(InvalidCouponCodeError):
            CouponCode("BIENVENIDA-10")

    def test_rejects_accented_characters(self) -> None:
        with pytest.raises(InvalidCouponCodeError):
            CouponCode("ÑOÑO10")


class TestCouponCodeInCoupon:
    def test_coupon_normalizes_code_on_creation(self) -> None:
        coupon = Coupon(
            coupon_code=CouponCode("  oferta20 "),
            coupon_type=CouponType.PERCENTAGE,
            amount=Decimal("20"),
            available_uses=10,
        )
        assert coupon.coupon_code.value == "OFERTA20"