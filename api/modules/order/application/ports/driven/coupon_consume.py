"""Driven port: consume one use of a coupon when the order is confirmed."""
from abc import ABC, abstractmethod


class CouponConsumePort(ABC):
    @abstractmethod
    def consume(self, coupon_code: str) -> None:
        ...
