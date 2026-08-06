"""GetCouponByCodeUseCase — fetch a single coupon by its code (admin)."""

from __future__ import annotations

from modules.config_coupon.application.ports.driver.coupon_admin_ports import (
    CouponSummary,
    GetCouponByCodePort,
    GetCouponByCodeQuery,
)
from modules.config_coupon.application.ports.driven.coupon_repository_port import (
    CouponRepositoryPort,
)
from modules.config_coupon.domain.errors.coupon_errors import CouponNotFoundError
from modules.config_coupon.domain.models.coupon_code import CouponCode


class GetCouponByCodeUseCase(GetCouponByCodePort):
    def __init__(self, coupon_repository: CouponRepositoryPort) -> None:
        self._coupon_repository = coupon_repository

    def execute(self, query: GetCouponByCodeQuery) -> CouponSummary:
        coupon_code = CouponCode(query.coupon_code)

        coupon = self._coupon_repository.find_by_code(coupon_code.value)
        if coupon is None:
            raise CouponNotFoundError(coupon_code.value)

        return CouponSummary(
            coupon_id=coupon.coupon_id or "",
            coupon_code=coupon.coupon_code.value,
            coupon_type=coupon.coupon_type.value,
            amount=coupon.amount,
            available_uses=coupon.available_uses,
            min_order_amount=coupon.min_order_amount,
            date_of_expiration=coupon.date_of_expiration,
            is_active=coupon.is_active,
        )