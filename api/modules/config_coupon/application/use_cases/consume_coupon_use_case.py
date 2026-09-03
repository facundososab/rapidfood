"""ConsumeCouponUseCase — consume one global use of a coupon.

Called by the ORDER module when the order leaves BORRADOR -> PENDIENTE (Q2).
The coupon's global use counter is decremented ONLY at confirmation, not when
the coupon is merely applied to a draft.

Enforcement: at consumption time the coupon must still be active and not
expired, so an exhausted/paused/expired coupon is never consumed. (The
min-order check belongs to ValidateCouponUseCase at draft time, where the
subtotal is known.)
"""

from __future__ import annotations

from modules.config_coupon.application.ports.driver.coupon_application_ports import (
    ConsumeCouponCommand,
    ConsumeCouponPort,
    ConsumeCouponResponse,
)
from modules.config_coupon.application.ports.driven.clock_port import ClockPort
from modules.config_coupon.application.ports.driven.coupon_repository_port import (
    CouponRepositoryPort,
)
from modules.config_coupon.domain.errors.coupon_errors import CouponNotFoundError
from modules.config_coupon.domain.models.coupon_code import CouponCode


class ConsumeCouponUseCase(ConsumeCouponPort):
    def __init__(
        self,
        coupon_repository: CouponRepositoryPort,
        clock: ClockPort,
    ) -> None:
        self._coupon_repository = coupon_repository
        self._clock = clock

    def execute(self, command: ConsumeCouponCommand) -> ConsumeCouponResponse:
        coupon_code = CouponCode(command.coupon_code)

        coupon = self._coupon_repository.find_by_code(coupon_code.value)
        if coupon is None:
            raise CouponNotFoundError(coupon_code.value)

        now = self._clock.utc_now()
        coupon.validate_consumable(now)
        coupon.consume_use()
        saved = self._coupon_repository.save(coupon)

        return ConsumeCouponResponse(
            coupon_code=saved.coupon_code.value,
            remaining_uses=saved.available_uses,
        )