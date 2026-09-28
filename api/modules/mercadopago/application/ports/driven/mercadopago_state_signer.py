"""Driven port: signing and validating the OAuth ``state`` parameter.

The state round-trips through the payer's browser, so it must be tamper-proof
and short-lived. It also carries the PKCE ``code_verifier``: the panel starts
the flow (where the value is generated) and Mercado Pago sends the browser back
to a different request (where the value is needed), so the signed state is the
only place the two share.

The algorithm (and its secret) is an infrastructure concern; the application
only needs to seal those two values and read them back.
"""

from dataclasses import dataclass
from typing import Protocol


@dataclass(frozen=True)
class SignedState:
    """What a valid OAuth ``state`` proves about the start of the flow."""

    business_config_id: str
    code_verifier: str | None = None


class MercadoPagoStateSignerPort(Protocol):
    def sign(
        self,
        business_config_id: str,
        code_verifier: str | None = None,
    ) -> str:
        """Seal the business configuration id and the PKCE verifier into a state."""
        ...

    def unsign(self, state: str) -> SignedState:
        """Return the sealed values, or fail for invalid/expired states."""
        ...
