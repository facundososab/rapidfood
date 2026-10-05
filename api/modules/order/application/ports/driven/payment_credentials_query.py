"""Driven port: per-business payment credentials used by the payment provider.

Implemented by an app-level cross-context adapter that reads the Mercado Pago
linkage of a business. A missing credential is not an error: the payment flow
falls back to the globally configured token.
"""

from abc import ABC, abstractmethod
from typing import Optional


class PaymentCredentialsQuery(ABC):
    @abstractmethod
    def get_access_token(self, business_config_id: str) -> Optional[str]:
        """Return the linked access token of a business, or ``None`` when absent."""
        pass
