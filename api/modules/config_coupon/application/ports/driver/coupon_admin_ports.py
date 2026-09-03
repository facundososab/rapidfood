"""Coupon admin driver ports — operations exposed to the business admin.

Commands/queries/responses are frozen dataclasses (plain Python). The
Protocols are the inbound contract implemented by use cases.
"""

from __future__ import annotations

from dataclasses import dataclass
from datetime import datetime
from decimal import Decimal
from typing import Protocol


@dataclass(frozen=True, slots=True)
class CreateCouponCommand:
    """Request to create a new coupon.

    Attributes:
        coupon_code: code (normalized to uppercase on creation).
        coupon_type: "FIXED_AMOUNT" | "PERCENTAGE".
        amount: fixed amount or percentage value.
        available_uses: total GLOBAL uses of the coupon.
        min_order_amount: required subtotal minimum (FIXED_AMOUNT only).
        date_of_expiration: last valid day (expires at 23:59:59 of that day).
        is_active: initial administrative state.
    """

    coupon_code: str
    coupon_type: str
    amount: Decimal
    available_uses: int
    min_order_amount: Decimal | None = None
    date_of_expiration: datetime | None = None
    is_active: bool = True


@dataclass(frozen=True, slots=True)
class CreateCouponResponse:
    coupon_id: str
    coupon_code: str
    coupon_type: str
    amount: Decimal
    available_uses: int
    min_order_amount: Decimal | None
    date_of_expiration: datetime | None
    is_active: bool


class CreateCouponPort(Protocol):
    def execute(self, command: CreateCouponCommand) -> CreateCouponResponse: ...


@dataclass(frozen=True, slots=True)
class ToggleCouponStatusCommand:
    coupon_id: str
    is_active: bool


@dataclass(frozen=True, slots=True)
class ToggleCouponStatusResponse:
    coupon_id: str
    is_active: bool


class ToggleCouponStatusPort(Protocol):
    def execute(self, command: ToggleCouponStatusCommand) -> ToggleCouponStatusResponse: ...


@dataclass(frozen=True, slots=True)
class ListCouponsQuery:
    """No filters for now — admin list of all coupons."""


@dataclass(frozen=True, slots=True)
class CouponSummary:
    coupon_id: str
    coupon_code: str
    coupon_type: str
    amount: Decimal
    available_uses: int
    min_order_amount: Decimal | None
    date_of_expiration: datetime | None
    is_active: bool


@dataclass(frozen=True, slots=True)
class ListCouponsResponse:
    coupons: tuple[CouponSummary, ...]


class ListCouponsPort(Protocol):
    def execute(self, query: ListCouponsQuery) -> ListCouponsResponse: ...


@dataclass(frozen=True, slots=True)
class GetCouponByCodeQuery:
    coupon_code: str


class GetCouponByCodePort(Protocol):
    def execute(self, query: GetCouponByCodeQuery) -> CouponSummary: ...