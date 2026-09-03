"""CreateCouponUseCase — admin creates a new coupon.

Orchestration:
1. Build + validate the domain value objects (code, type).
2. Ensure the code is unique.
3. Build the Coupon entity (enforces its own invariants).
4. Persist via the repository port.
5. Return the created coupon.
"""

from __future__ import annotations

from modules.config_coupon.application.ports.driver.coupon_admin_ports import (
    CreateCouponCommand,
    CreateCouponPort,
    CreateCouponResponse,
)
from modules.config_coupon.application.ports.driven.coupon_repository_port import (
    CouponRepositoryPort,
)
from modules.config_coupon.domain.errors.coupon_errors import CouponAlreadyExistsError
from modules.config_coupon.domain.models.coupon import Coupon
from modules.config_coupon.domain.models.coupon_code import CouponCode
from modules.config_coupon.domain.models.coupon_type import CouponType


class CreateCouponUseCase(CreateCouponPort):
    def __init__(self, coupon_repository: CouponRepositoryPort) -> None:
        self._coupon_repository = coupon_repository

    def execute(self, command: CreateCouponCommand) -> CreateCouponResponse:
        coupon_code = CouponCode(command.coupon_code)
        coupon_type = CouponType.from_value(command.coupon_type)

        if self._coupon_repository.find_by_code(coupon_code.value) is not None:
            raise CouponAlreadyExistsError(coupon_code.value)

        coupon = Coupon(
            coupon_code=coupon_code,
            coupon_type=coupon_type,
            amount=command.amount,
            available_uses=command.available_uses,
            min_order_amount=command.min_order_amount,
            date_of_expiration=command.date_of_expiration,
            is_active=command.is_active,
        )

        saved = self._coupon_repository.save(coupon)

        return CreateCouponResponse(
            coupon_id=saved.coupon_id or "",
            coupon_code=saved.coupon_code.value,
            coupon_type=saved.coupon_type.value,
            amount=saved.amount,
            available_uses=saved.available_uses,
            min_order_amount=saved.min_order_amount,
            date_of_expiration=saved.date_of_expiration,
            is_active=saved.is_active,
        )