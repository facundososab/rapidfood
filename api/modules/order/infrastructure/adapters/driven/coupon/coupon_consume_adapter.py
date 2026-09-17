"""Adapts the config_coupon module's consume port to the order module's port."""
from __future__ import annotations

from typing import Any

from modules.config_coupon.application.ports.driver.coupon_application_ports import (
    ConsumeCouponCommand,
)
from modules.order.application.ports.driven.coupon_consume import CouponConsumePort


class CouponConsumeAdapter(CouponConsumePort):
    def __init__(self, consume_coupon: Any) -> None:
        self._consume_coupon = consume_coupon

    def consume(self, coupon_code: str) -> None:
        self._consume_coupon.execute(ConsumeCouponCommand(coupon_code=coupon_code))
