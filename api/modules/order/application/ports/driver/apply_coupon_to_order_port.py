from abc import ABC, abstractmethod
from dataclasses import dataclass
from typing import Optional, Tuple


@dataclass
class ApplyCouponToOrderCommand:
    business_config_id: str
    order_id: str
    external_message_id: str
    coupon_code: str
    conversation_id: Optional[str] = None


@dataclass
class ApplyCouponToOrderResponse:
    order_id: str
    coupon_code: str
    discount_applied: str
    total_amount: str
    version: int
    replayed: bool = False
    superseded_attempt_ids: Tuple[str, ...] = ()


class ApplyCouponToOrderPort(ABC):
    @abstractmethod
    def execute(self, command: ApplyCouponToOrderCommand) -> ApplyCouponToOrderResponse:
        pass
