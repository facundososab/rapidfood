"""Driven port: the Mercado Pago OAuth endpoints.

The application needs three capabilities from Mercado Pago:

- generate the PKCE ``code_verifier``/``code_challenge`` pair,
- build the authorization URL the payer's browser is redirected to, and
- exchange the returned ``code`` for account tokens.

The PKCE pair is generated through this port (not by the use case) so the
application layer never imports infrastructure helpers, and the values are
sealed in the signed ``state`` for the callback to reuse.
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
    def generate_pkce_pair(self) -> tuple[str, str]:
        """Return a fresh PKCE pair as ``(code_verifier, code_challenge)``."""
        ...

    def build_authorization_url(
        self,
        state: str,
        code_challenge: str | None = None,
    ) -> str:
        """Return the Mercado Pago authorization URL carrying ``state``.

        ``code_challenge`` selects the PKCE flow (S256) when given.
        """
        ...

    def exchange_code(
        self,
        code: str,
        redirect_uri: str | None = None,
        code_verifier: str | None = None,
    ) -> OAuthTokenResult:
        """Exchange an authorization ``code`` for the account tokens.

        ``code_verifier`` proves possession of the PKCE secret when the
        authorization request used PKCE.
        """
        ...
