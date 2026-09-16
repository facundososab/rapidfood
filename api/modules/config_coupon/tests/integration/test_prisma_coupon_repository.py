"""Integration tests for PrismaCouponRepository (requires the test DB).

These tests exercise the real Prisma adapter against the dedicated Postgres
test database (marked ``db``). They require the project's normal environment
(``uv run pytest`` with Postgres up) — they are NOT runnable in a bare env.
"""

from __future__ import annotations

from datetime import datetime, timezone
from decimal import Decimal

import pytest

from modules.config_coupon.domain.models.coupon import Coupon
from modules.config_coupon.domain.models.coupon_code import CouponCode
from modules.config_coupon.domain.models.coupon_type import CouponType
from modules.config_coupon.infrastructure.adapters.driven.prisma.prisma_coupon_repository import (
    PrismaCouponRepository,
)
from shared.infrastructure.prisma.db import Database

pytestmark = pytest.mark.db


def _utc(y: int, m: int, d: int) -> datetime:
    return datetime(y, m, d, tzinfo=timezone.utc)


class _TestDatabase(Database):
    """Wraps the pytest ``db`` fixture client so the repository targets the
    dedicated test database instead of the shared dev singleton."""

    def __init__(self, client: object) -> None:
        super().__init__()
        self._client = client  # type: ignore[assignment]


@pytest.fixture(autouse=True)
def _clean_coupons(db):
    """Delete leftover coupons from previous tests (self-cleaning)."""
    yield
    db.coupon.delete_many(where={})


class TestPrismaCouponRepository:
    def test_save_and_find_by_code(self, db) -> None:
        repo = PrismaCouponRepository(_TestDatabase(db))
        coupon = Coupon(
            coupon_code=CouponCode("OFERTA10"),
            coupon_type=CouponType.PERCENTAGE,
            amount=Decimal("10"),
            available_uses=100,
        )

        saved = repo.save(coupon)

        assert saved.coupon_id is not None
        found = repo.find_by_code("OFERTA10")
        assert found is not None
        assert found.coupon_code.value == "OFERTA10"
        assert found.amount == Decimal("10")
        assert found.available_uses == 100
        assert found.is_active is True

    def test_saves_fixed_amount_with_min_order_and_expiration(self, db) -> None:
        repo = PrismaCouponRepository(_TestDatabase(db))
        coupon = Coupon(
            coupon_code=CouponCode("FIJOS"),
            coupon_type=CouponType.FIXED_AMOUNT,
            amount=Decimal("5000"),
            available_uses=5,
            min_order_amount=Decimal("10000"),
            date_of_expiration=_utc(2026, 12, 31),
        )

        repo.save(coupon)
        found = repo.find_by_code("FIJOS")

        assert found is not None
        assert found.min_order_amount == Decimal("10000")
        assert found.date_of_expiration is not None
        assert found.date_of_expiration.date() == _utc(2026, 12, 31).date()

    def test_update_persists_changes(self, db) -> None:
        repo = PrismaCouponRepository(_TestDatabase(db))
        coupon = Coupon(
            coupon_code=CouponCode("OFERTA10"),
            coupon_type=CouponType.PERCENTAGE,
            amount=Decimal("10"),
            available_uses=5,
        )
        saved = repo.save(coupon)

        saved.available_uses = 4
        repo.save(saved)

        found = repo.find_by_code("OFERTA10")
        assert found is not None
        assert found.available_uses == 4

    def test_find_by_id(self, db) -> None:
        repo = PrismaCouponRepository(_TestDatabase(db))
        saved = repo.save(
            Coupon(
                coupon_code=CouponCode("OFERTA10"),
                coupon_type=CouponType.PERCENTAGE,
                amount=Decimal("10"),
                available_uses=100,
            )
        )

        found = repo.find_by_id(saved.coupon_id or "")

        assert found is not None
        assert found.coupon_code.value == "OFERTA10"

    def test_list_all_orders_by_code(self, db) -> None:
        repo = PrismaCouponRepository(_TestDatabase(db))
        repo.save(
            Coupon(
                coupon_code=CouponCode("BETA"),
                coupon_type=CouponType.PERCENTAGE,
                amount=Decimal("10"),
                available_uses=5,
            )
        )
        repo.save(
            Coupon(
                coupon_code=CouponCode("ALFA"),
                coupon_type=CouponType.PERCENTAGE,
                amount=Decimal("10"),
                available_uses=5,
            )
        )

        coupons = repo.list_all()

        assert [c.coupon_code.value for c in coupons] == ["ALFA", "BETA"]

    def test_returns_none_when_not_found(self, db) -> None:
        repo = PrismaCouponRepository(_TestDatabase(db))
        assert repo.find_by_code("NOEXISTE") is None
        assert repo.find_by_id("00000000-0000-0000-0000-000000000000") is None
