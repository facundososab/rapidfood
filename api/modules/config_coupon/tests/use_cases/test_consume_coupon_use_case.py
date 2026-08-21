"""Tests for ConsumeCouponUseCase."""

from __future__ import annotations

from datetime import datetime, timezone
from decimal import Decimal

import pytest

from modules.config_coupon.application.ports.driver.coupon_application_ports import (
    ConsumeCouponCommand,
)
from modules.config_coupon.application.use_cases.consume_coupon_use_case import (
    ConsumeCouponUseCase,
)
from modules.config_coupon.domain.errors.coupon_errors import (
    CouponDepletedError,
    CouponExpiredError,
    CouponInactiveError,
    CouponNotFoundError,
)
from modules.config_coupon.domain.models.coupon import Coupon
from modules.config_coupon.domain.models.coupon_code import CouponCode
from modules.config_coupon.domain.models.coupon_type import CouponType
from modules.config_coupon.tests.use_cases.fakes import FixedClock, InMemoryCouponRepository


def _utc(y: int, m: int, d: int) -> datetime:
    return datetime(y, m, d, tzinfo=timezone.utc)


def _coupon(**overrides: object) -> Coupon:
    base: dict[str, object] = {
        "coupon_code": CouponCode("OFERTA10"),
        "coupon_type": CouponType.PERCENTAGE,
        "amount": Decimal("10"),
        "available_uses": 5,
    }
    base.update(overrides)
    return Coupon(**base)


class TestConsumeCoupon:
    def _setup(self, coupon: Coupon) -> tuple[ConsumeCouponUseCase, InMemoryCouponRepository]:
        repo = InMemoryCouponRepository()
        repo.save(coupon)
        clock = FixedClock(_utc(2026, 8, 1))
        return ConsumeCouponUseCase(repo, clock), repo

    def test_decrements_global_uses(self) -> None:
        uc, repo = self._setup(_coupon(available_uses=5))

        result = uc.execute(ConsumeCouponCommand("OFERTA10"))

        assert result.remaining_uses == 4
        assert repo.find_by_code("OFERTA10").available_uses == 4

    def test_unknown_coupon_raises(self) -> None:
        repo = InMemoryCouponRepository()
        uc = ConsumeCouponUseCase(repo, FixedClock(_utc(2026, 8, 1)))
        with pytest.raises(CouponNotFoundError):
            uc.execute(ConsumeCouponCommand("NOEXISTE"))

    def test_depleted_coupon_not_consumed(self) -> None:
        uc, repo = self._setup(_coupon(available_uses=0))
        with pytest.raises(CouponDepletedError):
            uc.execute(ConsumeCouponCommand("OFERTA10"))

    def test_inactive_coupon_not_consumed(self) -> None:
        uc, _ = self._setup(_coupon(is_active=False))
        with pytest.raises(CouponInactiveError):
            uc.execute(ConsumeCouponCommand("OFERTA10"))

    def test_expired_coupon_not_consumed(self) -> None:
        uc, _ = self._setup(_coupon(date_of_expiration=_utc(2026, 7, 31)))
        with pytest.raises(CouponExpiredError):
            uc.execute(ConsumeCouponCommand("OFERTA10"))

    def test_fixed_amount_coupon_can_be_consumed_without_min_order_recheck(
        self,
    ) -> None:
        # Min order was validated at draft time; consumption must not re-check it.
        uc, repo = self._setup(
            _coupon(
                coupon_type=CouponType.FIXED_AMOUNT,
                amount=Decimal("5000"),
                available_uses=3,
                min_order_amount=Decimal("10000"),
            )
        )

        result = uc.execute(ConsumeCouponCommand("OFERTA10"))

        assert result.remaining_uses == 2