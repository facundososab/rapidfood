"""ToggleCouponStatusUseCase — pause or re-activate a coupon.

Administrative operation (REQ-005 / Q4): the ``is_active`` flag explicitly
pauses a coupon without deleting it. Paused coupons fail validation.
"""

from __future__ import annotations

from modules.config_coupon.application.ports.driver.coupon_admin_ports import (
    ToggleCouponStatusCommand,
    ToggleCouponStatusPort,
    ToggleCouponStatusResponse,
)
from modules.config_coupon.application.ports.driven.coupon_repository_port import (
    CouponRepositoryPort,
)
from modules.config_coupon.domain.errors.coupon_errors import CouponNotFoundError


class ToggleCouponStatusUseCase(ToggleCouponStatusPort):
    def __init__(self, coupon_repository: CouponRepositoryPort) -> None:
        self._coupon_repository = coupon_repository

    def execute(self, command: ToggleCouponStatusCommand) -> ToggleCouponStatusResponse:
        coupon = self._coupon_repository.find_by_id(command.coupon_id)
        if coupon is None:
            raise CouponNotFoundError(command.coupon_id)

        if command.is_active:
            coupon.activate()
        else:
            coupon.pause()

        saved = self._coupon_repository.save(coupon)

        return ToggleCouponStatusResponse(
            coupon_id=saved.coupon_id or "",
            is_active=saved.is_active,
        )