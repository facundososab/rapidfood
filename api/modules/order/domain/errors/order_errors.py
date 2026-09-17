class OrderDomainError(Exception):
    """Base class for all order domain errors."""
    pass


class OrderStateError(OrderDomainError):
    """Raised when an operation is invalid for the current order state."""
    pass


class InvalidPaymentTypeError(OrderDomainError):
    """Raised when a payment type outside CASH | ONLINE is provided."""
    pass


class PaymentAttemptNotFoundError(OrderDomainError):
    """Raised when a payment attempt referenced by id or provider id is unknown."""
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


class NewOrderRequiredError(OrderNotModifiableError):
    """Raised when the current order cannot be modified and a new order is needed.

    Examples: the order is paid/confirmed/cancelled/cash-pending, or a payment
    for its current version was already approved. The previous order MUST be
    left untouched; starting a new order is a separate, explicit flow.
    """
    reason = "NEW_ORDER_REQUIRED"


class InvalidCouponError(CouponApplicationError):
    """Raised when the coupon itself is invalid."""
    pass


class BusinessClosedError(OrderDomainError):
    """Raised when the business is not accepting orders right now."""
    pass


class MinimumOrderNotMetError(OrderDomainError):
    """Raised when the order subtotal is below the configured minimum."""
    pass


class OrderClientRequiredError(OrderDomainError):
    """Raised when an order is confirmed with no client reference (id or name)."""
    pass


class DeliveryNotAvailableError(OrderDomainError):
    """Raised when the destination is outside the delivery zone or delivery is not configured."""
    pass


class DeliveryAddressRequiredError(OrderDomainError):
    """Raised when a DELIVERY order is configured without a destination address."""
    pass


class DeliveryQuoteFailedError(OrderDomainError):
    """Raised when the delivery provider could not produce a quote."""
    pass


class IngredientNotRemovableError(OrderDomainError):
    """Raised when a client tries to remove a non-removable ingredient."""
    pass


class ModifierValidationError(OrderDomainError):
    """Raised when modifier selection violates group rules."""
    pass