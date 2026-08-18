from abc import ABC, abstractmethod
from dataclasses import dataclass
from decimal import Decimal
from typing import Optional


@dataclass
class CouponSnapshot:
    coupon_code: str
    discount_amount: Decimal
    is_valid: bool


class CouponQueryPort(ABC):
    @abstractmethod
    def validate_coupon(self, coupon_code: str, order_subtotal: Decimal) -> Optional[CouponSnapshot]:
        pass
