"""Order errors as part of the DRIVER-PORT contract.

Re-exported from the domain so a cross-context adapter can catch order errors
without importing the order module's domain internals (the architecture only
allows `*.application.ports.**` across bounded contexts).

Mapping a caught error to a business code is the adapter's job; this module only
declares the vocabulary.
"""
from modules.order.domain.errors.order_errors import (  # noqa: F401
    BusinessClosedError,
    CouponApplicationError,
    DeliveryAddressRequiredError,
    DeliveryNotAvailableError,
    DeliveryQuoteFailedError,
    IngredientNotRemovableError,
    InvalidCouponError,
    InvalidLineError,
    InvalidPaymentTypeError,
    MinimumOrderNotMetError,
    ModifierValidationError,
    NewOrderRequiredError,
    OrderClientRequiredError,
    OrderDomainError,
    OrderNotFound,
    OrderNotModifiableError,
    OrderStateError,
    PaymentAttemptNotFoundError,
)

__all__ = [
    "BusinessClosedError",
    "CouponApplicationError",
    "DeliveryAddressRequiredError",
    "DeliveryNotAvailableError",
    "DeliveryQuoteFailedError",
    "IngredientNotRemovableError",
    "InvalidCouponError",
    "InvalidLineError",
    "InvalidPaymentTypeError",
    "MinimumOrderNotMetError",
    "ModifierValidationError",
    "NewOrderRequiredError",
    "OrderClientRequiredError",
    "OrderDomainError",
    "OrderNotFound",
    "OrderNotModifiableError",
    "OrderStateError",
    "PaymentAttemptNotFoundError",
]
