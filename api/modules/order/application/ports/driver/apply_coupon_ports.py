from abc import ABC, abstractmethod
from dataclasses import dataclass
from typing import Optional

@dataclass
class ApplyCouponCommand:
    order_id: str
    coupon_code: str


@dataclass
class ApplyCouponResponse:
    order_id: str
    coupon_code: str
    discount_applied: str
    total_amount: str


class ApplyCouponPort(ABC):
    @abstractmethod
    def apply(self, command: ApplyCouponCommand) -> ApplyCouponResponse:
        pass
