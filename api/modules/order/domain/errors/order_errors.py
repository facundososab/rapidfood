class OrderDomainError(Exception):
    """Base class for all order domain errors."""
    pass

class OrderStateError(OrderDomainError):
    """Raised when an operation is invalid for the current order state."""
    pass

class OrderNotFound(OrderDomainError):
    """Raised when an order is not found."""
    pass

class InvalidLineError(OrderDomainError):
    """Raised when a line is invalid (e.g. quantity < 1)."""
    pass

class CouponApplicationError(OrderDomainError):
    """Raised when a coupon cannot be applied."""
    pass
