"""Driven port: the Mercado Pago OAuth endpoints.

The application needs two capabilities from Mercado Pago:

- build the authorization URL the payer's browser is redirected to, and
- exchange the returned ``code`` for account tokens.
"""

from dataclasses import dataclass
from typing import Protocol


@dataclass(frozen=True)
class OAuthTokenResult:
    """Tokens and account identity returned by the OAuth token endpoint."""

    access_token: str
    refresh_token: str | None = None
    user_id: str | None = None
    public_key: str | None = None
    live_mode: bool = False


class MercadoPagoOAuthClientPort(Protocol):
    def build_authorization_url(self, state: str) -> str:
        """Return the Mercado Pago authorization URL carrying ``state``."""
        ...

    def exchange_code(self, code: str, redirect_uri: str | None = None) -> OAuthTokenResult:
        """Exchange an authorization ``code`` for the account tokens."""
        ...
