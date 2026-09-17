from modules.order.application.ports.driven.applied_coupon_repository import (
    AppliedCouponRepositoryPort,
)
from modules.order.application.ports.driver.list_applied_coupons_ports import (
    AppliedCouponItem,
    ListAppliedCouponsPort,
    ListAppliedCouponsQuery,
)


class ListAppliedCouponsUseCase(ListAppliedCouponsPort):
    def __init__(self, applied_coupon_repo: AppliedCouponRepositoryPort) -> None:
        self._repo = applied_coupon_repo

    def execute(self, query: ListAppliedCouponsQuery) -> list[AppliedCouponItem]:
        return [
            AppliedCouponItem(
                id=row.id,
                order_id=row.order_id,
                coupon_id=row.coupon_id,
                coupon_code=row.coupon_code,
                coupon_type=row.coupon_type,
                amount=row.amount,
                discount_amount=row.discount_amount,
                available_uses=row.available_uses,
                date_of_expiration=row.date_of_expiration,
                applied_at=row.applied_at,
            )
            for row in self._repo.list_by_coupon(query.coupon_id)
        ]
