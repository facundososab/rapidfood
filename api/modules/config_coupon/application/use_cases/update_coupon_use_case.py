"""UpdateCouponUseCase — admin edits an existing coupon.

Code and type are immutable (they are the coupon's identity); the editable
fields are amount, available uses, minimum order, expiration and active state.
The entity is rebuilt so its invariants are re-validated before persisting.
"""

from __future__ import annotations

from modules.config_coupon.application.ports.driver.coupon_admin_ports import (
    UpdateCouponCommand,
    UpdateCouponPort,
    UpdateCouponResponse,
)
from modules.config_coupon.application.ports.driven.coupon_repository_port import (
    CouponRepositoryPort,
)
from modules.config_coupon.domain.errors.coupon_errors import CouponNotFoundError
from modules.config_coupon.domain.models.coupon import Coupon


class UpdateCouponUseCase(UpdateCouponPort):
    def __init__(self, coupon_repository: CouponRepositoryPort) -> None:
        self._coupon_repository = coupon_repository

    def execute(self, command: UpdateCouponCommand) -> UpdateCouponResponse:
        existing = self._coupon_repository.find_by_id(command.coupon_id)
        if existing is None:
            raise CouponNotFoundError(command.coupon_id)

        updated = Coupon(
            coupon_id=existing.coupon_id,
            coupon_code=existing.coupon_code,
            coupon_type=existing.coupon_type,
            amount=command.amount,
            available_uses=command.available_uses,
            min_order_amount=command.min_order_amount,
            date_of_expiration=command.date_of_expiration,
            is_active=command.is_active,
        )

        saved = self._coupon_repository.save(updated)

        return UpdateCouponResponse(
            coupon_id=saved.coupon_id or "",
            coupon_code=saved.coupon_code.value,
            coupon_type=saved.coupon_type.value,
            amount=saved.amount,
            available_uses=saved.available_uses,
            min_order_amount=saved.min_order_amount,
            date_of_expiration=saved.date_of_expiration,
            is_active=saved.is_active,
        )
