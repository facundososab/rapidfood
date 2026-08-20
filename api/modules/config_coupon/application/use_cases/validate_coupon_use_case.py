"""ValidateCouponUseCase — validate a coupon against an order subtotal.

Called by the ORDER module (or the agent) while the order is BORRADOR
(REQ-020). It:

1. Loads the coupon by code.
2. Validates applicability against the subtotal (active, uses, expiration,
   min order).
3. Calculates the exact discount amount.

This does NOT consume a use — consumption happens on BORRADOR -> PENDIENTE
via ConsumeCouponUseCase (Q2).
"""

from __future__ import annotations

from modules.config_coupon.application.ports.driver.coupon_application_ports import (
    ValidateCouponCommand,
    ValidateCouponPort,
    ValidateCouponResponse,
)
from modules.config_coupon.application.ports.driven.clock_port import ClockPort
from modules.config_coupon.application.ports.driven.coupon_repository_port import (
    CouponRepositoryPort,
)
from modules.config_coupon.domain.errors.coupon_errors import CouponNotFoundError
from modules.config_coupon.domain.models.coupon_code import CouponCode


class ValidateCouponUseCase(ValidateCouponPort):
    def __init__(
        self,
        coupon_repository: CouponRepositoryPort,
        clock: ClockPort,
    ) -> None:
        self._coupon_repository = coupon_repository
        self._clock = clock

    def execute(self, command: ValidateCouponCommand) -> ValidateCouponResponse:
        coupon_code = CouponCode(command.coupon_code)

        coupon = self._coupon_repository.find_by_code(coupon_code.value)
        if coupon is None:
            raise CouponNotFoundError(coupon_code.value)

        now = self._clock.utc_now()
        coupon.validate_applicable(command.subtotal, now)
        discount_amount = coupon.calculate_discount(command.subtotal)

        return ValidateCouponResponse(
            coupon_id=coupon.coupon_id or "",
            coupon_code=coupon.coupon_code.value,
            coupon_type=coupon.coupon_type.value,
            amount=coupon.amount,
            discount_amount=discount_amount,
            available_uses=coupon.available_uses,
            date_of_expiration=coupon.date_of_expiration,
        )