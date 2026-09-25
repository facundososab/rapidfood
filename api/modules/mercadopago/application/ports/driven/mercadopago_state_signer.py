"""Driven port: signing and validating the OAuth ``state`` parameter.

The state round-trips through the payer's browser, so it must be tamper-proof
and short-lived. The algorithm (and its secret) is an infrastructure concern;
the application only needs to seal a business id and read it back.
"""

from typing import Protocol


class MercadoPagoStateSignerPort(Protocol):
    def sign(self, business_config_id: str) -> str:
        """Seal the business configuration id into an OAuth state token."""
        ...

    def unsign(self, state: str) -> str:
        """Return the business configuration id, or fail for invalid/expired states."""
        ...
