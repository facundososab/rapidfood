"""Tests for ToggleCouponStatusUseCase."""

from __future__ import annotations

from decimal import Decimal

import pytest

from modules.config_coupon.application.ports.driver.coupon_admin_ports import (
    ToggleCouponStatusCommand,
)
from modules.config_coupon.application.use_cases.toggle_coupon_status_use_case import (
    ToggleCouponStatusUseCase,
)
from modules.config_coupon.domain.errors.coupon_errors import CouponNotFoundError
from modules.config_coupon.domain.models.coupon import Coupon
from modules.config_coupon.domain.models.coupon_code import CouponCode
from modules.config_coupon.domain.models.coupon_type import CouponType
from modules.config_coupon.tests.use_cases.fakes import InMemoryCouponRepository


class TestToggleCouponStatus:
    def _setup(self) -> tuple[ToggleCouponStatusUseCase, InMemoryCouponRepository, str]:
        repo = InMemoryCouponRepository()
        saved = repo.save(
            Coupon(
                coupon_code=CouponCode("OFERTA10"),
                coupon_type=CouponType.PERCENTAGE,
                amount=Decimal("10"),
                available_uses=100,
            )
        )
        return ToggleCouponStatusUseCase(repo), repo, saved.coupon_id or ""

    def test_pauses_coupon(self) -> None:
        uc, repo, coupon_id = self._setup()
        result = uc.execute(ToggleCouponStatusCommand(coupon_id, False))
        assert result.is_active is False
        assert repo.find_by_id(coupon_id).is_active is False

    def test_reactivates_coupon(self) -> None:
        uc, repo, coupon_id = self._setup()
        uc.execute(ToggleCouponStatusCommand(coupon_id, False))
        result = uc.execute(ToggleCouponStatusCommand(coupon_id, True))
        assert result.is_active is True
        assert repo.find_by_id(coupon_id).is_active is True

    def test_unknown_coupon_raises(self) -> None:
        uc, _, _ = self._setup()
        with pytest.raises(CouponNotFoundError):
            uc.execute(ToggleCouponStatusCommand("missing", False))