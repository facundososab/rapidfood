from abc import ABC, abstractmethod
from dataclasses import dataclass
from datetime import datetime
from decimal import Decimal
from typing import Optional


@dataclass
class CouponSnapshot:
    coupon_code: str
    discount_amount: Decimal
    is_valid: bool
    coupon_id: Optional[str] = None
    coupon_type: Optional[str] = None
    amount: Optional[Decimal] = None
    available_uses: Optional[int] = None
    date_of_expiration: Optional[datetime] = None


class CouponQueryPort(ABC):
    @abstractmethod
    def validate_coupon(self, coupon_code: str, order_subtotal: Decimal) -> Optional[CouponSnapshot]:
        pass
