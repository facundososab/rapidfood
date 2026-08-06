"""ListCouponsUseCase — list all coupons for the admin (REQ-005)."""

from __future__ import annotations

from modules.config_coupon.application.ports.driver.coupon_admin_ports import (
    CouponSummary,
    ListCouponsPort,
    ListCouponsQuery,
    ListCouponsResponse,
)
from modules.config_coupon.application.ports.driven.coupon_repository_port import (
    CouponRepositoryPort,
)


class ListCouponsUseCase(ListCouponsPort):
    def __init__(self, coupon_repository: CouponRepositoryPort) -> None:
        self._coupon_repository = coupon_repository

    def execute(self, query: ListCouponsQuery) -> ListCouponsResponse:
        coupons = self._coupon_repository.list_all()
        return ListCouponsResponse(
            coupons=tuple(
                CouponSummary(
                    coupon_id=coupon.coupon_id or "",
                    coupon_code=coupon.coupon_code.value,
                    coupon_type=coupon.coupon_type.value,
                    amount=coupon.amount,
                    available_uses=coupon.available_uses,
                    min_order_amount=coupon.min_order_amount,
                    date_of_expiration=coupon.date_of_expiration,
                    is_active=coupon.is_active,
                )
                for coupon in coupons
            )
        )