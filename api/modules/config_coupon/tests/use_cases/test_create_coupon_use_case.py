"""Tests for CreateCouponUseCase."""

from __future__ import annotations

from decimal import Decimal

import pytest

from modules.config_coupon.application.ports.driver.coupon_admin_ports import (
    CreateCouponCommand,
)
from modules.config_coupon.application.use_cases.create_coupon_use_case import (
    CreateCouponUseCase,
)
from modules.config_coupon.domain.errors.coupon_errors import (
    CouponAlreadyExistsError,
    InvalidCouponAmountError,
    InvalidCouponTypeError,
)
from modules.config_coupon.tests.use_cases.fakes import InMemoryCouponRepository


def _cmd(**overrides: object) -> CreateCouponCommand:
    base: dict[str, object] = {
        "coupon_code": "OFERTA10",
        "coupon_type": "PERCENTAGE",
        "amount": Decimal("10"),
        "available_uses": 100,
    }
    base.update(overrides)
    return CreateCouponCommand(**base)  # type: ignore[arg-type]


class TestCreateCoupon:
    def test_creates_percentage_coupon(self) -> None:
        repo = InMemoryCouponRepository()
        uc = CreateCouponUseCase(repo)

        result = uc.execute(_cmd())

        assert result.coupon_code == "OFERTA10"
        assert result.coupon_type == "PERCENTAGE"
        assert result.amount == Decimal("10")
        assert result.available_uses == 100
        assert result.is_active is True
        assert result.coupon_id != ""

    def test_creates_fixed_amount_coupon_with_min_order(self) -> None:
        repo = InMemoryCouponRepository()
        uc = CreateCouponUseCase(repo)

        result = uc.execute(
            _cmd(
                coupon_code="FIJOS",
                coupon_type="FIXED_AMOUNT",
                amount=Decimal("5000"),
                available_uses=5,
                min_order_amount=Decimal("10000"),
            )
        )

        assert result.coupon_type == "FIXED_AMOUNT"
        assert result.min_order_amount == Decimal("10000")

    def test_saves_coupon_to_repository(self) -> None:
        repo = InMemoryCouponRepository()
        uc = CreateCouponUseCase(repo)

        uc.execute(_cmd())

        assert len(repo.list_all()) == 1

    def test_duplicate_code_raises(self) -> None:
        repo = InMemoryCouponRepository()
        uc = CreateCouponUseCase(repo)
        uc.execute(_cmd())

        with pytest.raises(CouponAlreadyExistsError):
            uc.execute(_cmd())

    def test_invalid_coupon_type_raises(self) -> None:
        uc = CreateCouponUseCase(InMemoryCouponRepository())
        with pytest.raises(InvalidCouponTypeError):
            uc.execute(_cmd(coupon_type="FREE"))

    def test_fixed_amount_without_min_order_raises(self) -> None:
        uc = CreateCouponUseCase(InMemoryCouponRepository())
        with pytest.raises(InvalidCouponAmountError):
            uc.execute(_cmd(coupon_type="FIXED_AMOUNT", amount=Decimal("5000")))

    def test_normalizes_code_before_save(self) -> None:
        repo = InMemoryCouponRepository()
        uc = CreateCouponUseCase(repo)

        uc.execute(_cmd(coupon_code="  oferta10 "))

        assert repo.find_by_code("OFERTA10") is not None