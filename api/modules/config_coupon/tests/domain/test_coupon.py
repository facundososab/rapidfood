"""Domain tests for the Coupon entity â€” the core business rules.

These encode the invariants agreed with the business owner (Q1-Q4):
- Fixed-amount coupons require a min order; percentage coupons have no cap.
- Discount applies to the subtotal.
- Coupons expire at the END of the day (23:59:59).
- Uses are a global counter, consumed at BORRADOR -> PENDIENTE.
- is_active explicitly pauses a coupon.
"""

from __future__ import annotations

from datetime import datetime, timezone
from decimal import Decimal

import pytest

from modules.config_coupon.domain.errors.coupon_errors import (
    CouponDepletedError,
    CouponExpiredError,
    CouponInactiveError,
    CouponMinOrderNotReachedError,
    InvalidCouponAmountError,
    InvalidCouponUsesError,
)
from modules.config_coupon.domain.models.coupon import Coupon
from modules.config_coupon.domain.models.coupon_code import CouponCode
from modules.config_coupon.domain.models.coupon_type import CouponType


def _make_coupon(**overrides: object) -> Coupon:
    base: dict[str, object] = {
        "coupon_code": CouponCode("OFERTA10"),
        "coupon_type": CouponType.PERCENTAGE,
        "amount": Decimal("10"),
        "available_uses": 100,
    }
    base.update(overrides)
    return Coupon(**base)


def _utc(y: int, m: int, d: int, h: int = 12) -> datetime:
    return datetime(y, m, d, h, tzinfo=timezone.utc)


class TestCouponCreationInvariants:
    def test_fixed_amount_requires_min_order(self) -> None:
        with pytest.raises(InvalidCouponAmountError):
            _make_coupon(coupon_type=CouponType.FIXED_AMOUNT, amount=Decimal("5000"))

    def test_fixed_amount_accepts_min_order(self) -> None:
        Coupon(
            coupon_code=CouponCode("FIJOS"),
            coupon_type=CouponType.FIXED_AMOUNT,
            amount=Decimal("5000"),
            available_uses=5,
            min_order_amount=Decimal("10000"),
        )

    def test_percentage_amount_must_not_exceed_100(self) -> None:
        with pytest.raises(InvalidCouponAmountError):
            _make_coupon(coupon_type=CouponType.PERCENTAGE, amount=Decimal("150"))

    def test_percentage_has_no_min_order_required(self) -> None:
        # Percentage coupons need NO min_order_amount (Q1).
        _make_coupon(coupon_type=CouponType.PERCENTAGE, amount=Decimal("10"))

    def test_non_positive_amount_rejected(self) -> None:
        with pytest.raises(InvalidCouponAmountError):
            _make_coupon(amount=Decimal("0"))

    def test_negative_uses_rejected(self) -> None:
        with pytest.raises(InvalidCouponUsesError):
            _make_coupon(available_uses=-1)


class TestCouponExpiration:
    def test_no_expiration_never_expires(self) -> None:
        coupon = _make_coupon(date_of_expiration=None)
        assert not coupon.is_expired(_utc(2999, 1, 1))

    def test_expires_after_end_of_expiration_day(self) -> None:
        # Expires 2026-08-10 at 23:59:59.
        coupon = _make_coupon(date_of_expiration=_utc(2026, 8, 10))
        assert coupon.is_expired(_utc(2026, 8, 11))  # next day
        assert coupon.is_expired(_utc(2026, 8, 11, 0, ))  # even at 00:00

    def test_valid_all_day_on_expiration_date(self) -> None:
        coupon = _make_coupon(date_of_expiration=_utc(2026, 8, 10))
        assert not coupon.is_expired(_utc(2026, 8, 10, 23))  # 23:00 same day
        assert not coupon.is_expired(_utc(2026, 8, 10, 0))  # 00:00 same day

    def test_valid_after_expiration_date(self) -> None:
        coupon = _make_coupon(date_of_expiration=_utc(2026, 8, 10))
        assert not coupon.is_expired(_utc(2026, 8, 9))


class TestCouponApplicability:
    def test_inactive_coupon_rejected(self) -> None:
        coupon = _make_coupon(is_active=False)
        with pytest.raises(CouponInactiveError):
            coupon.validate_applicable(Decimal("1000"), _utc(2026, 8, 1))

    def test_depleted_coupon_rejected(self) -> None:
        coupon = _make_coupon(available_uses=0)
        with pytest.raises(CouponDepletedError):
            coupon.validate_applicable(Decimal("1000"), _utc(2026, 8, 1))

    def test_expired_coupon_rejected(self) -> None:
        coupon = _make_coupon(date_of_expiration=_utc(2026, 8, 10))
        with pytest.raises(CouponExpiredError):
            coupon.validate_applicable(Decimal("1000"), _utc(2026, 8, 11))

    def test_fixed_amount_below_min_order_rejected(self) -> None:
        coupon = Coupon(
            coupon_code=CouponCode("FIJOS"),
            coupon_type=CouponType.FIXED_AMOUNT,
            amount=Decimal("5000"),
            available_uses=5,
            min_order_amount=Decimal("10000"),
        )
        with pytest.raises(CouponMinOrderNotReachedError):
            coupon.validate_applicable(Decimal("9999"), _utc(2026, 8, 1))

    def test_fixed_amount_reaching_min_order_accepted(self) -> None:
        coupon = Coupon(
            coupon_code=CouponCode("FIJOS"),
            coupon_type=CouponType.FIXED_AMOUNT,
            amount=Decimal("5000"),
            available_uses=5,
            min_order_amount=Decimal("10000"),
        )
        coupon.validate_applicable(Decimal("10000"), _utc(2026, 8, 1))  # no raise

    def test_percentage_valid(self) -> None:
        coupon = _make_coupon(coupon_type=CouponType.PERCENTAGE, amount=Decimal("10"))
        coupon.validate_applicable(Decimal("1000"), _utc(2026, 8, 1))  # no raise


class TestCouponDiscount:
    def test_percentage_discount_no_cap(self) -> None:
        # Q1: percentage has no cap.
        coupon = _make_coupon(coupon_type=CouponType.PERCENTAGE, amount=Decimal("50"))
        assert coupon.calculate_discount(Decimal("10000")) == Decimal("5000.00")

    def test_percentage_rounds_half_up(self) -> None:
        coupon = _make_coupon(coupon_type=CouponType.PERCENTAGE, amount=Decimal("33.33"))
        # 9999 * 33.33% = 3332.6667 -> rounds half-up to 3332.67
        assert coupon.calculate_discount(Decimal("9999")) == Decimal("3332.67")

    def test_fixed_amount_capped_by_subtotal(self) -> None:
        # Q1: discount never exceeds the subtotal.
        coupon = Coupon(
            coupon_code=CouponCode("FIJOS"),
            coupon_type=CouponType.FIXED_AMOUNT,
            amount=Decimal("5000"),
            available_uses=5,
            min_order_amount=Decimal("1000"),
        )
        assert coupon.calculate_discount(Decimal("4000")) == Decimal("4000.00")

    def test_fixed_amount_full_value_when_subtotal_big_enough(self) -> None:
        coupon = Coupon(
            coupon_code=CouponCode("FIJOS"),
            coupon_type=CouponType.FIXED_AMOUNT,
            amount=Decimal("5000"),
            available_uses=5,
            min_order_amount=Decimal("1000"),
        )
        assert coupon.calculate_discount(Decimal("10000")) == Decimal("5000.00")


class TestCouponUseConsumption:
    def test_consume_decrements_counter(self) -> None:
        coupon = _make_coupon(available_uses=2)
        coupon.consume_use()
        assert coupon.available_uses == 1
        coupon.consume_use()
        assert coupon.available_uses == 0

    def test_consume_beyond_zero_raises(self) -> None:
        coupon = _make_coupon(available_uses=1)
        coupon.consume_use()
        with pytest.raises(CouponDepletedError):
            coupon.consume_use()


class TestCouponConsumable:
    def test_consumable_when_valid(self) -> None:
        coupon = _make_coupon(available_uses=5)
        coupon.validate_consumable(_utc(2026, 8, 1))  # no raise

    def test_consumable_ignores_min_order(self) -> None:
        # Min order is NOT re-checked at consumption (already validated at draft).
        coupon = Coupon(
            coupon_code=CouponCode("FIJOS"),
            coupon_type=CouponType.FIXED_AMOUNT,
            amount=Decimal("5000"),
            available_uses=5,
            min_order_amount=Decimal("10000"),
        )
        coupon.validate_consumable(_utc(2026, 8, 1))  # no raise

    def test_inactive_not_consumable(self) -> None:
        coupon = _make_coupon(is_active=False)
        with pytest.raises(CouponInactiveError):
            coupon.validate_consumable(_utc(2026, 8, 1))

    def test_depleted_not_consumable(self) -> None:
        coupon = _make_coupon(available_uses=0)
        with pytest.raises(CouponDepletedError):
            coupon.validate_consumable(_utc(2026, 8, 1))

    def test_expired_not_consumable(self) -> None:
        coupon = _make_coupon(date_of_expiration=_utc(2026, 8, 10))
        with pytest.raises(CouponExpiredError):
            coupon.validate_consumable(_utc(2026, 8, 11))


class TestCouponStatus:
    def test_pause_sets_inactive(self) -> None:
        coupon = _make_coupon()
        coupon.pause()
        assert coupon.is_active is False

    def test_activate_reactivates(self) -> None:
        coupon = _make_coupon(is_active=False)
        coupon.activate()
        assert coupon.is_active is True