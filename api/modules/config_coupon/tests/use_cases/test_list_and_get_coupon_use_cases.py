"""Tests for ListCouponsUseCase and GetCouponByCodeUseCase."""

from __future__ import annotations

from decimal import Decimal

import pytest

from modules.config_coupon.application.ports.driver.coupon_admin_ports import (
    GetCouponByCodeQuery,
    ListCouponsQuery,
)
from modules.config_coupon.application.use_cases.get_coupon_by_code_use_case import (
    GetCouponByCodeUseCase,
)
from modules.config_coupon.application.use_cases.list_coupons_use_case import (
    ListCouponsUseCase,
)
from modules.config_coupon.domain.errors.coupon_errors import CouponNotFoundError
from modules.config_coupon.domain.models.coupon import Coupon
from modules.config_coupon.domain.models.coupon_code import CouponCode
from modules.config_coupon.domain.models.coupon_type import CouponType
from modules.config_coupon.tests.use_cases.fakes import InMemoryCouponRepository


class TestListCoupons:
    def test_lists_all_coupons(self) -> None:
        repo = InMemoryCouponRepository()
        repo.save(
            Coupon(
                coupon_code=CouponCode("A"),
                coupon_type=CouponType.PERCENTAGE,
                amount=Decimal("10"),
                available_uses=5,
            )
        )
        repo.save(
            Coupon(
                coupon_code=CouponCode("B"),
                coupon_type=CouponType.FIXED_AMOUNT,
                amount=Decimal("5000"),
                available_uses=3,
                min_order_amount=Decimal("10000"),
            )
        )

        result = ListCouponsUseCase(repo).execute(ListCouponsQuery())

        assert len(result.coupons) == 2
        assert result.coupons[0].coupon_code == "A"
        assert result.coupons[0].min_order_amount is None
        assert result.coupons[1].min_order_amount == Decimal("10000")


class TestGetCouponByCode:
    def test_returns_coupon(self) -> None:
        repo = InMemoryCouponRepository()
        repo.save(
            Coupon(
                coupon_code=CouponCode("OFERTA10"),
                coupon_type=CouponType.PERCENTAGE,
                amount=Decimal("10"),
                available_uses=100,
            )
        )

        result = GetCouponByCodeUseCase(repo).execute(GetCouponByCodeQuery("OFERTA10"))

        assert result.coupon_code == "OFERTA10"
        assert result.amount == Decimal("10")

    def test_normalizes_code_in_query(self) -> None:
        repo = InMemoryCouponRepository()
        repo.save(
            Coupon(
                coupon_code=CouponCode("OFERTA10"),
                coupon_type=CouponType.PERCENTAGE,
                amount=Decimal("10"),
                available_uses=100,
            )
        )
        result = GetCouponByCodeUseCase(repo).execute(
            GetCouponByCodeQuery("  oferta10 ")
        )
        assert result.coupon_code == "OFERTA10"

    def test_unknown_coupon_raises(self) -> None:
        uc = GetCouponByCodeUseCase(InMemoryCouponRepository())
        with pytest.raises(CouponNotFoundError):
            uc.execute(GetCouponByCodeQuery("NOEXISTE"))