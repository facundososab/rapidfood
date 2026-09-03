"""Tests for ValidateCouponUseCase."""

from __future__ import annotations

from datetime import datetime, timezone
from decimal import Decimal

import pytest

from modules.config_coupon.application.ports.driver.coupon_application_ports import (
    ValidateCouponCommand,
)
from modules.config_coupon.application.use_cases.validate_coupon_use_case import (
    ValidateCouponUseCase,
)
from modules.config_coupon.domain.errors.coupon_errors import (
    CouponDepletedError,
    CouponExpiredError,
    CouponInactiveError,
    CouponMinOrderNotReachedError,
    CouponNotFoundError,
)
from modules.config_coupon.domain.models.coupon import Coupon
from modules.config_coupon.domain.models.coupon_code import CouponCode
from modules.config_coupon.domain.models.coupon_type import CouponType
from modules.config_coupon.tests.use_cases.fakes import FixedClock, InMemoryCouponRepository


def _utc(y: int, m: int, d: int) -> datetime:
    return datetime(y, m, d, tzinfo=timezone.utc)


class TestValidateCoupon:
    def _setup(self, coupon: Coupon | None = None) -> tuple[ValidateCouponUseCase, InMemoryCouponRepository]:
        repo = InMemoryCouponRepository()
        if coupon is not None:
            repo.save(coupon)
        clock = FixedClock(_utc(2026, 8, 1))
        return ValidateCouponUseCase(repo, clock), repo

    def test_returns_discount_for_percentage(self) -> None:
        coupon = Coupon(
            coupon_code=CouponCode("OFERTA10"),
            coupon_type=CouponType.PERCENTAGE,
            amount=Decimal("10"),
            available_uses=100,
        )
        uc, _ = self._setup(coupon)

        result = uc.execute(ValidateCouponCommand("OFERTA10", Decimal("1000")))

        assert result.coupon_code == "OFERTA10"
        assert result.discount_amount == Decimal("100.00")
        assert result.coupon_type == "PERCENTAGE"
        assert result.available_uses == 100

    def test_returns_discount_for_fixed_amount(self) -> None:
        coupon = Coupon(
            coupon_code=CouponCode("FIJOS"),
            coupon_type=CouponType.FIXED_AMOUNT,
            amount=Decimal("5000"),
            available_uses=5,
            min_order_amount=Decimal("10000"),
        )
        uc, _ = self._setup(coupon)

        result = uc.execute(ValidateCouponCommand("FIJOS", Decimal("20000")))

        assert result.discount_amount == Decimal("5000.00")

    def test_unknown_coupon_raises(self) -> None:
        uc, _ = self._setup()
        with pytest.raises(CouponNotFoundError):
            uc.execute(ValidateCouponCommand("NOEXISTE", Decimal("1000")))

    def test_inactive_coupon_raises(self) -> None:
        coupon = Coupon(
            coupon_code=CouponCode("PAUSADO"),
            coupon_type=CouponType.PERCENTAGE,
            amount=Decimal("10"),
            available_uses=100,
            is_active=False,
        )
        uc, _ = self._setup(coupon)
        with pytest.raises(CouponInactiveError):
            uc.execute(ValidateCouponCommand("PAUSADO", Decimal("1000")))

    def test_depleted_coupon_raises(self) -> None:
        coupon = Coupon(
            coupon_code=CouponCode("AGOTADO"),
            coupon_type=CouponType.PERCENTAGE,
            amount=Decimal("10"),
            available_uses=0,
        )
        uc, _ = self._setup(coupon)
        with pytest.raises(CouponDepletedError):
            uc.execute(ValidateCouponCommand("AGOTADO", Decimal("1000")))

    def test_expired_coupon_raises(self) -> None:
        coupon = Coupon(
            coupon_code=CouponCode("VENCIDO"),
            coupon_type=CouponType.PERCENTAGE,
            amount=Decimal("10"),
            available_uses=100,
            date_of_expiration=_utc(2026, 7, 31),
        )
        uc, _ = self._setup(coupon)
        with pytest.raises(CouponExpiredError):
            uc.execute(ValidateCouponCommand("VENCIDO", Decimal("1000")))

    def test_min_order_not_reached_raises(self) -> None:
        coupon = Coupon(
            coupon_code=CouponCode("FIJOS"),
            coupon_type=CouponType.FIXED_AMOUNT,
            amount=Decimal("5000"),
            available_uses=5,
            min_order_amount=Decimal("10000"),
        )
        uc, _ = self._setup(coupon)
        with pytest.raises(CouponMinOrderNotReachedError):
            uc.execute(ValidateCouponCommand("FIJOS", Decimal("5000")))

    def test_does_not_consume_a_use(self) -> None:
        # Q2: applying to a draft does NOT consume a use.
        coupon = Coupon(
            coupon_code=CouponCode("OFERTA10"),
            coupon_type=CouponType.PERCENTAGE,
            amount=Decimal("10"),
            available_uses=100,
        )
        uc, repo = self._setup(coupon)

        uc.execute(ValidateCouponCommand("OFERTA10", Decimal("1000")))

        assert repo.find_by_code("OFERTA10").available_uses == 100