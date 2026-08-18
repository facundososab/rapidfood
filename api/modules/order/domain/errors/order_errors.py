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

class OrderNotModifiableError(OrderDomainError):
    """Raised when an order cannot be modified in its current state."""
    pass

class InvalidCouponError(OrderDomainError):
    """Raised when a coupon is invalid for an order."""
    pass

class BusinessClosedError(OrderDomainError):
    """Raised when an order cannot be confirmed because the business is closed."""
    pass

class MinimumOrderNotMetError(OrderDomainError):
    """Raised when an order total is below the configured minimum."""
    pass
