"""Fakes shared by the order payment use-case tests.

The credentials fake never touches the linkage module: like the real adapter it
answers with a plain token or ``None``, and it can be configured to fail so the
fallback paths can be asserted.
"""

from __future__ import annotations

from typing import Optional

from modules.order.application.ports.driven.payment_credentials_query import (
    PaymentCredentialsQuery,
)


class FakePaymentCredentialsQuery(PaymentCredentialsQuery):
    """In-memory PaymentCredentialsQuery that records the requested businesses."""

    def __init__(
        self,
        tokens: Optional[dict[str, str]] = None,
        error: Optional[Exception] = None,
    ) -> None:
        self.tokens = dict(tokens or {})
        self.error = error
        self.requested: list[str] = []

    def get_access_token(self, business_config_id: str) -> Optional[str]:
        self.requested.append(business_config_id)
        if self.error is not None:
            raise self.error
        return self.tokens.get(business_config_id)
