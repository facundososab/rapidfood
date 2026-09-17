"""Driven port: persist and read applied-coupon records (order history)."""
from abc import ABC, abstractmethod
from dataclasses import dataclass
from datetime import datetime
from decimal import Decimal
from typing import Optional


@dataclass
class AppliedCouponSnapshot:
    order_id: str
    coupon_code: str
    coupon_type: str
    amount: Decimal
    discount_amount: Decimal
    available_uses: int
    applied_at: datetime
    id: Optional[str] = None
    coupon_id: Optional[str] = None
    date_of_expiration: Optional[datetime] = None


class AppliedCouponRepositoryPort(ABC):
    @abstractmethod
    def add(self, snapshot: AppliedCouponSnapshot) -> AppliedCouponSnapshot:
        ...

    @abstractmethod
    def list_by_coupon(self, coupon_id: str) -> list[AppliedCouponSnapshot]:
        ...
