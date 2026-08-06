"""Composition root for the config_coupon module.

Instantiates concrete driven adapters (Prisma repository, system clock) and
injects them into every use case. Views and other modules obtain the use cases
through this container — never by constructing repositories/adapter themselves.

The shared Prisma lazy singleton (``shared.infrastructure.prisma.db``) is the
single data-layer connection injected into the repository.
"""

from __future__ import annotations

from functools import lru_cache

from modules.config_coupon.application.use_cases.consume_coupon_use_case import (
    ConsumeCouponUseCase,
)
from modules.config_coupon.application.use_cases.create_coupon_use_case import (
    CreateCouponUseCase,
)
from modules.config_coupon.application.use_cases.get_coupon_by_code_use_case import (
    GetCouponByCodeUseCase,
)
from modules.config_coupon.application.use_cases.list_coupons_use_case import (
    ListCouponsUseCase,
)
from modules.config_coupon.application.use_cases.toggle_coupon_status_use_case import (
    ToggleCouponStatusUseCase,
)
from modules.config_coupon.application.use_cases.validate_coupon_use_case import (
    ValidateCouponUseCase,
)
from modules.config_coupon.infrastructure.adapters.driven.prisma.prisma_coupon_repository import (
    PrismaCouponRepository,
)
from modules.config_coupon.infrastructure.adapters.driven.prisma.system_clock import (
    SystemClock,
)
from shared.infrastructure.prisma.db import db


class CouponContainer:
    """Wires concrete dependencies into the coupon use cases."""

    def __init__(self) -> None:
        coupon_repository = PrismaCouponRepository(db.client)
        clock = SystemClock()

        self.create_coupon = CreateCouponUseCase(coupon_repository)
        self.validate_coupon = ValidateCouponUseCase(coupon_repository, clock)
        self.consume_coupon = ConsumeCouponUseCase(coupon_repository, clock)
        self.toggle_coupon_status = ToggleCouponStatusUseCase(coupon_repository)
        self.list_coupons = ListCouponsUseCase(coupon_repository)
        self.get_coupon_by_code = GetCouponByCodeUseCase(coupon_repository)


@lru_cache(maxsize=1)
def get_coupon_container() -> CouponContainer:
    """Return the module's singleton composition root."""
    return CouponContainer()