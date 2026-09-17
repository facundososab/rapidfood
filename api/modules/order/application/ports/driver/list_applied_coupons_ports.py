from abc import ABC, abstractmethod
from dataclasses import dataclass
from datetime import datetime
from decimal import Decimal
from typing import Optional


@dataclass
class ListAppliedCouponsQuery:
    coupon_id: str


@dataclass
class AppliedCouponItem:
    id: str
    order_id: str
    coupon_code: str
    coupon_type: str
    amount: Decimal
    discount_amount: Decimal
    available_uses: int
    applied_at: datetime
    coupon_id: Optional[str] = None
    date_of_expiration: Optional[datetime] = None


class ListAppliedCouponsPort(ABC):
    @abstractmethod
    def execute(self, query: ListAppliedCouponsQuery) -> list[AppliedCouponItem]:
        ...
