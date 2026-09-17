from datetime import datetime
from decimal import Decimal
from typing import Optional

from modules.order.application.ports.driven.applied_coupon_repository import (
    AppliedCouponRepositoryPort,
    AppliedCouponSnapshot,
)
from modules.order.application.ports.driver.apply_coupon_ports import (
    ApplyCouponPort, ApplyCouponCommand, ApplyCouponResponse
)
from modules.order.application.ports.driven.order_repository import OrderRepository
from modules.order.application.ports.driven.coupon_query import CouponQueryPort
from modules.order.domain.errors.order_errors import OrderNotFound, OrderNotModifiableError, InvalidCouponError
from modules.order.domain.models.order_state import OrderState


class ApplyCouponUseCase(ApplyCouponPort):
    def __init__(
        self,
        order_repo: OrderRepository,
        coupon_query: CouponQueryPort,
        applied_coupon_repo: Optional[AppliedCouponRepositoryPort] = None,
    ):
        self.order_repo = order_repo
        self.coupon_query = coupon_query
        self.applied_coupon_repo = applied_coupon_repo

    def apply(self, command: ApplyCouponCommand) -> ApplyCouponResponse:
        order = self.order_repo.get_by_id(command.order_id)
        if not order:
            raise OrderNotFound("Order not found")

        if order.status != OrderState.DRAFT:
            raise OrderNotModifiableError("Coupons can only be applied to DRAFT orders")

        if not order.lines:
            raise InvalidCouponError("Cannot apply coupon to an empty order")

        coupon = self.coupon_query.validate_coupon(command.coupon_code, order.subtotal)

        if not coupon or not coupon.is_valid:
            raise InvalidCouponError(f"Coupon {command.coupon_code} is invalid or expired")

        # Global discount applied to the order. We keep the coupon reference and the
        # exact code so the use can be consumed when the order leaves DRAFT.
        order.discount = coupon.discount_amount
        order.applied_coupon_id = coupon.coupon_id
        order.coupon_code = coupon.coupon_code

        order._recalculate_totals()

        if self.applied_coupon_repo is not None:
            self.applied_coupon_repo.add(
                AppliedCouponSnapshot(
                    order_id=order.id,
                    coupon_id=coupon.coupon_id,
                    coupon_code=coupon.coupon_code,
                    coupon_type=coupon.coupon_type or "",
                    amount=coupon.amount or Decimal("0"),
                    discount_amount=coupon.discount_amount,
                    available_uses=coupon.available_uses or 0,
                    date_of_expiration=coupon.date_of_expiration,
                    applied_at=datetime.utcnow(),
                )
            )

        self.order_repo.save(order)

        return ApplyCouponResponse(
            order_id=order.id,
            coupon_code=command.coupon_code,
            discount_applied=str(order.discount),
            total_amount=str(order.total_amount)
        )
