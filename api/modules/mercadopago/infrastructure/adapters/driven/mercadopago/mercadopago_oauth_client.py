"""MercadoPagoOAuthClient — the OAuth endpoints of Mercado Pago.

Responsibilities, all over HTTP plus local crypto:

- ``generate_pkce_pair`` produces the RFC 7636 (S256) pair,
- ``build_authorization_url`` builds the URL the payer's browser is sent to,
  carrying a signed ``state``, the application's ``client_id`` and the PKCE
  challenge, and
- ``exchange_code`` performs the classic ``POST /oauth/token`` form exchange,
  with the PKCE verifier instead of the client secret when the application has
  no secret (Mercado Pago marks ``client_secret`` optional for PKCE flows).

The ``requests`` module (or any object exposing ``post``) is injected so tests
exercise the exact request without touching the network.
"""

from __future__ import annotations

import base64
import hashlib
import os
import secrets
from dataclasses import dataclass
from typing import Any
from urllib.parse import urlencode

import requests

from modules.mercadopago.application.ports.driven.mercadopago_oauth_client import (
    OAuthTokenResult,
)
from modules.mercadopago.domain.errors.mercadopago_errors import (
    MercadoPagoConfigurationError,
    MercadoPagoOAuthError,
)

DEFAULT_AUTH_BASE_URL = "https://auth.mercadopago.com"
DEFAULT_API_BASE_URL = "https://api.mercadopago.com"
DEFAULT_TIMEOUT_SECONDS = 10.0

# RFC 7636 section 4.1: 32 random bytes encode to 43 unpadded base64url chars.
PKCE_VERIFIER_BYTES = 32
PKCE_CHALLENGE_METHOD = "S256"

# Error codes/messages are truncated so a misbehaving upstream cannot flood logs.
_MAX_ERROR_DETAIL_LENGTH = 200


def generate_pkce_verifier() -> str:
    """Return a fresh RFC 7636 ``code_verifier`` (43 base64url chars, no padding)."""
    return secrets.token_urlsafe(PKCE_VERIFIER_BYTES)


def generate_pkce_challenge(verifier: str) -> str:
    """Return the S256 ``code_challenge`` for ``verifier`` (base64url, no padding)."""
    digest = hashlib.sha256(verifier.encode("ascii")).digest()
    return base64.urlsafe_b64encode(digest).rstrip(b"=").decode("ascii")


@dataclass
class MercadoPagoOAuthSettings:
    """OAuth application settings, read from the environment by ``from_env``."""

    client_id: str | None = None
    client_secret: str | None = None
    redirect_uri: str | None = None
    return_uri: str | None = None
    auth_base_url: str = DEFAULT_AUTH_BASE_URL
    api_base_url: str = DEFAULT_API_BASE_URL
    timeout_seconds: float = DEFAULT_TIMEOUT_SECONDS

    @classmethod
    def from_env(cls) -> "MercadoPagoOAuthSettings":
        return cls(
            client_id=os.environ.get("MERCADOPAGO_CLIENT_ID") or None,
            client_secret=os.environ.get("MERCADOPAGO_CLIENT_SECRET") or None,
            redirect_uri=os.environ.get("MERCADOPAGO_REDIRECT_URI") or None,
            return_uri=os.environ.get("MERCADOPAGO_RETURN_URI") or None,
            auth_base_url=os.environ.get("MERCADOPAGO_AUTH_BASE_URL", DEFAULT_AUTH_BASE_URL),
            api_base_url=os.environ.get("MERCADOPAGO_API_BASE_URL", DEFAULT_API_BASE_URL),
        )


class MercadoPagoOAuthClient:
    def __init__(
        self,
        settings: MercadoPagoOAuthSettings,
        http: Any | None = None,
    ) -> None:
        self._settings = settings
        self._http = http if http is not None else requests

    def generate_pkce_pair(self) -> tuple[str, str]:
        verifier = generate_pkce_verifier()
        return verifier, generate_pkce_challenge(verifier)

    def build_authorization_url(
        self,
        state: str,
        code_challenge: str | None = None,
    ) -> str:
        client_id = self.require_client_id()
        redirect_uri = self.require_redirect_uri()

        params = {
            "client_id": client_id,
            "response_type": "code",
            "platform_id": "mp",
            "redirect_uri": redirect_uri,
            "state": state,
        }
        if code_challenge:
            params["code_challenge"] = code_challenge
            params["code_challenge_method"] = PKCE_CHALLENGE_METHOD

        query = urlencode(params)
        return f"{self._settings.auth_base_url.rstrip('/')}/authorization?{query}"

    def exchange_code(
        self,
        code: str,
        redirect_uri: str | None = None,
        code_verifier: str | None = None,
    ) -> OAuthTokenResult:
        client_id = self.require_client_id()
        target_redirect_uri = redirect_uri or self.require_redirect_uri()

        url = f"{self._settings.api_base_url.rstrip('/')}/oauth/token"
        form = {
            "grant_type": "authorization_code",
            "client_id": client_id,
            "code": code,
            "redirect_uri": target_redirect_uri,
        }
        # Mercado Pago marks client_secret optional for PKCE authorization
        # requests; sending an empty value is not the same as omitting it.
        client_secret = (self._settings.client_secret or "").strip()
        if client_secret:
            form["client_secret"] = client_secret
        if code_verifier:
            form["code_verifier"] = code_verifier

        body = self._post_form(url, form)

        access_token = body.get("access_token")
        if not access_token:
            raise MercadoPagoOAuthError(self._rejection_message(body))

        return OAuthTokenResult(
            access_token=str(access_token),
            refresh_token=_optional_str(body.get("refresh_token")),
            user_id=_optional_str(body.get("user_id")),
            public_key=_optional_str(body.get("public_key")),
            live_mode=_as_bool(body.get("live_mode")),
        )

    # --- configuration guards ------------------------------------------------

    def require_client_id(self) -> str:
        client_id = (self._settings.client_id or "").strip()
        if not client_id:
            raise MercadoPagoConfigurationError(
                "Mercado Pago is not configured: MERCADOPAGO_CLIENT_ID is missing"
            )
        return client_id

    def require_redirect_uri(self) -> str:
        redirect_uri = (self._settings.redirect_uri or "").strip()
        if not redirect_uri:
            raise MercadoPagoConfigurationError(
                "Mercado Pago is not configured: MERCADOPAGO_REDIRECT_URI is missing"
            )
        return redirect_uri

    # --- HTTP ----------------------------------------------------------------

    def _post_form(self, url: str, form: dict[str, str]) -> dict[str, Any]:
        try:
            response = self._http.post(
                url,
                data=form,
                headers={"Accept": "application/json"},
                timeout=self._settings.timeout_seconds,
            )
            response.raise_for_status()
            body = response.json()
        except Exception as exc:
            raise MercadoPagoOAuthError(
                f"Mercado Pago token exchange failed: {exc}"
            ) from exc

        if not isinstance(body, dict):
            raise MercadoPagoOAuthError(
                "Mercado Pago token exchange returned an unexpected response"
            )
        return body

    def _rejection_message(self, body: dict[str, Any]) -> str:
        detail = body.get("error")
        message = "Mercado Pago rejected the token exchange"
        if detail:
            truncated = str(detail)[:_MAX_ERROR_DETAIL_LENGTH]
            message = f"{message}: {truncated}"
        return message


def _optional_str(value: Any) -> str | None:
    return None if value is None else str(value)


def _as_bool(value: Any) -> bool:
    if isinstance(value, bool):
        return value
    if isinstance(value, (int, float)):
        return value == 1
    if isinstance(value, str):
        return value.strip().lower() in {"true", "1", "yes"}
    return False
