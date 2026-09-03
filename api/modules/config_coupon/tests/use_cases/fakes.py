"""Shared fakes/stubs for use case tests (no infrastructure)."""

from __future__ import annotations

from datetime import datetime

from modules.config_coupon.application.ports.driven.clock_port import ClockPort
from modules.config_coupon.application.ports.driven.coupon_repository_port import (
    CouponRepositoryPort,
)
from modules.config_coupon.domain.models.coupon import Coupon


class InMemoryCouponRepository(CouponRepositoryPort):
    """Repository fake backed by an in-memory dict."""

    def __init__(self) -> None:
        self._by_id: dict[str, Coupon] = {}
        self._by_code: dict[str, Coupon] = {}
        self._next_id = 1

    def save(self, coupon: Coupon) -> Coupon:
        if coupon.coupon_id is None:
            coupon.coupon_id = f"coupon-{self._next_id}"
            self._next_id += 1
        self._by_id[coupon.coupon_id] = coupon
        self._by_code[coupon.coupon_code.value] = coupon
        return coupon

    def find_by_code(self, coupon_code: str) -> Coupon | None:
        return self._by_code.get(coupon_code)

    def find_by_id(self, coupon_id: str) -> Coupon | None:
        return self._by_id.get(coupon_id)

    def list_all(self) -> list[Coupon]:
        return list(self._by_id.values())


class FixedClock(ClockPort):
    """Clock that always returns a fixed instant (deterministic tests)."""

    def __init__(self, now: datetime) -> None:
        self._now = now

    def utc_now(self) -> datetime:
        return self._now