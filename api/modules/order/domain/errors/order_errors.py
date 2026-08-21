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
    """Raised when an order line is invalid (e.g. quantity < 1)."""
    pass


class CouponApplicationError(OrderDomainError):
    """Raised when a coupon cannot be applied."""
    pass


class OrderNotModifiableError(OrderStateError):
    """Raised when an operation is invalid because the order is not modifiable."""
    pass


class InvalidCouponError(CouponApplicationError):
    """Raised when the coupon itself is invalid."""
    pass


class BusinessClosedError(OrderDomainError):
    """Raised when the business is not accepting orders right now."""
    pass


class MinimumOrderNotMetError(OrderDomainError):
    """Raised when the order subtotal is below the configured minimum."""
    pass