"""Coupon query port — outbound (owned by ``apps.config_coupon``).

Contract only. Validity (dates/uses) is a use-case rule; this port only reads
coupon rows from the Prisma-managed database.
"""

from dataclasses import dataclass
from datetime import datetime
from decimal import Decimal
from typing import Protocol


@dataclass(frozen=True)
class CouponDTO:
    coupon_id: str
    coupon_code: str
    type: str
    amount: Decimal
    available_uses: int
    date_of_expiration: datetime | None


class CouponQueryPort(Protocol):
    def find_valid_by_code(self, code: str) -> CouponDTO | None: ...
    def find_by_id(self, coupon_id: str) -> CouponDTO | None: ...
