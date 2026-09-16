from enum import Enum


class PaymentStatus(str, Enum):
    PENDING = "PENDING"
    APPROVED = "APPROVED"
    REJECTED = "REJECTED"
    FAILED = "FAILED"
    EXPIRED = "EXPIRED"

    def is_final(self) -> bool:
        return self in {
            PaymentStatus.APPROVED,
            PaymentStatus.REJECTED,
            PaymentStatus.FAILED,
            PaymentStatus.EXPIRED,
        }
