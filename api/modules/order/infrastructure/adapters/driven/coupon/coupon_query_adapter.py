"""Adapts the config_coupon module's validate port to the order module's port.

Cross-context boundary: the coupon module's error hierarchy lives outside the
importable surface (only `application.ports` is shared), so an invalid coupon is
reported as `is_valid=False` instead of propagating the foreign exception.
"""
from __future__ import annotations

from decimal import Decimal
from typing import Any, Optional

from modules.config_coupon.application.ports.driver.coupon_application_ports import (
    ValidateCouponCommand,
)
from modules.order.application.ports.driven.coupon_query import (
    CouponQueryPort,
    CouponSnapshot,
)


class CouponQueryAdapter(CouponQueryPort):
    def __init__(self, validate_coupon: Any) -> None:
        self._validate_coupon = validate_coupon

    def validate_coupon(self, coupon_code: str, order_subtotal: Decimal) -> Optional[CouponSnapshot]:
        try:
            result = self._validate_coupon.execute(
                ValidateCouponCommand(coupon_code=coupon_code, subtotal=order_subtotal)
            )
        except Exception:
            return CouponSnapshot(
                coupon_code=coupon_code,
                discount_amount=Decimal("0"),
                is_valid=False,
            )
        return CouponSnapshot(
            coupon_code=result.coupon_code,
            discount_amount=result.discount_amount,
            is_valid=True,
            coupon_id=result.coupon_id,
            coupon_type=result.coupon_type,
            amount=result.amount,
            available_uses=result.available_uses,
            date_of_expiration=result.date_of_expiration,
        )
