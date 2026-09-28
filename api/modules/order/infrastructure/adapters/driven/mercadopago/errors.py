"""Backwards-compatible re-export of the provider error.

The error belongs to the application port (so use cases can catch it without
importing infrastructure); this module keeps existing imports working.
"""
from modules.order.application.ports.driven.payment_provider import (
    PaymentProviderError,
)

__all__ = ["PaymentProviderError"]
