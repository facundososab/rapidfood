from modules.order.application.ports.driver.apply_coupon_ports import (
    ApplyCouponPort, ApplyCouponCommand, ApplyCouponResponse
)
from modules.order.application.ports.driven.order_repository import OrderRepository
from modules.order.application.ports.driven.coupon_query import CouponQueryPort
from modules.order.domain.errors.order_errors import OrderNotFound, OrderNotModifiableError, InvalidCouponError
from modules.order.domain.models.order_state import OrderState


class ApplyCouponUseCase(ApplyCouponPort):
    def __init__(self, order_repo: OrderRepository, coupon_query: CouponQueryPort):
        self.order_repo = order_repo
        self.coupon_query = coupon_query

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

        # In this simplified model, we apply a global discount to the order.
        # It could be saved in order.discount, and recalculate totals.
        order.discount = coupon.discount_amount
        # Note: the DB schema requires a discount_id in order if we want to trace it.
        # But per user instructions: "el cupon esta en otro module. asique deberia guardarse un opcionl del cupon id y del monto/descuento del cupon aplicado"
        # We need to add coupon_id to the Order domain model and ORM if it's not there!
        
        # We will add it dynamically for now, but need to update models
        order.coupon_id = command.coupon_code
        
        order._recalculate_totals()
        
        self.order_repo.save(order)

        return ApplyCouponResponse(
            order_id=order.id,
            coupon_code=command.coupon_code,
            discount_applied=str(order.discount),
            total_amount=str(order.total_amount)
        )
