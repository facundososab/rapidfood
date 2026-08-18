from enum import Enum


class OrderState(str, Enum):
    """
    Represents the lifecycle state of an order (RN-001, RN-024).
    """
    DRAFT = "DRAFT"
    PENDING = "PENDING"
    PAID = "PAID"
    CONFIRMED = "CONFIRMED"
    IN_PREPARATION = "IN_PREPARATION"
    READY = "READY"
    DELIVERED = "DELIVERED"
    PICKED_UP = "PICKED_UP"
    CANCELLED = "CANCELLED"
