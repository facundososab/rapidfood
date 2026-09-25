"""Fakes for the Mercado Pago linkage use-case tests.

No network and no database: the repository is an in-memory dict, the OAuth
client records what it was asked for, and the state signer simulates tampering
and expiry with a movable clock.
"""

from __future__ import annotations

import time

from modules.mercadopago.application.ports.driven.mercadopago_oauth_client import (
    OAuthTokenResult,
)
from modules.mercadopago.domain.errors.mercadopago_errors import (
    MercadoPagoStateError,
)
from modules.mercadopago.domain.models.mercadopago_credential import (
    MercadoPagoCredential,
)

BUSINESS_CONFIG_ID = "11111111-1111-1111-1111-111111111111"
OTHER_BUSINESS_CONFIG_ID = "22222222-2222-2222-2222-222222222222"
GENERATED_CREDENTIAL_ID = "33333333-3333-3333-3333-333333333333"

AUTHORIZATION_BASE_URL = "https://auth.mercadopago.com/authorization"


class FakeMercadoPagoCredentialRepository:
    """In-memory MercadoPagoCredentialRepositoryPort."""

    def __init__(
        self,
        credentials: dict[str, MercadoPagoCredential] | None = None,
    ) -> None:
        self._credentials = dict(credentials or {})
        self.upserted: list[MercadoPagoCredential] = []
        self.deleted: list[str] = []

    def get_by_business(self, business_config_id: str) -> MercadoPagoCredential | None:
        return self._credentials.get(business_config_id)

    def upsert(self, credential: MercadoPagoCredential) -> MercadoPagoCredential:
        self.upserted.append(credential)
        stored = MercadoPagoCredential(
            credential_id=credential.credential_id or GENERATED_CREDENTIAL_ID,
            business_config_id=credential.business_config_id,
            access_token=credential.access_token,
            refresh_token=credential.refresh_token,
            user_id=credential.user_id,
            public_key=credential.public_key,
            live_mode=credential.live_mode,
        )
        self._credentials[stored.business_config_id] = stored
        return stored

    def delete(self, business_config_id: str) -> None:
        self.deleted.append(business_config_id)
        self._credentials.pop(business_config_id, None)


class FakeMercadoPagoOAuthClient:
    """Records the OAuth calls and returns a configured token result."""

    def __init__(
        self,
        tokens: OAuthTokenResult | None = None,
        authorize_error: Exception | None = None,
        exchange_error: Exception | None = None,
    ) -> None:
        self.tokens = tokens if tokens is not None else OAuthTokenResult(access_token="APP_USR-token")
        self.authorize_error = authorize_error
        self.exchange_error = exchange_error
        self.received_states: list[str] = []
        self.exchanged: list[tuple[str, str | None]] = []

    def build_authorization_url(self, state: str) -> str:
        if self.authorize_error is not None:
            raise self.authorize_error
        self.received_states.append(state)
        return f"{AUTHORIZATION_BASE_URL}?state={state}"

    def exchange_code(self, code: str, redirect_uri: str | None = None) -> OAuthTokenResult:
        self.exchanged.append((code, redirect_uri))
        if self.exchange_error is not None:
            raise self.exchange_error
        return self.tokens


class FakeStateSigner:
    """Signs states in-memory so tests can prove tampering and expiry handling."""

    def __init__(self, max_age_seconds: int = 600) -> None:
        self._max_age_seconds = max_age_seconds
        self._now = time.time()
        self._issued: dict[str, tuple[str, float]] = {}
        self.signed_business_ids: list[str] = []

    def sign(self, business_config_id: str) -> str:
        token = f"signed:{business_config_id}:{int(self._now)}"
        self._issued[token] = (business_config_id, self._now)
        self.signed_business_ids.append(business_config_id)
        return token

    def unsign(self, state: str) -> str:
        entry = self._issued.get(state)
        if entry is None:
            raise MercadoPagoStateError("Mercado Pago OAuth state is invalid")
        business_config_id, issued_at = entry
        if self._now - issued_at > self._max_age_seconds:
            raise MercadoPagoStateError("Mercado Pago OAuth state has expired")
        return business_config_id

    def advance(self, seconds: float) -> None:
        """Move the fake clock forward, aging every signed state."""
        self._now += seconds


def make_credential(**overrides) -> MercadoPagoCredential:
    values = {
        "business_config_id": BUSINESS_CONFIG_ID,
        "access_token": "APP_USR-stored-token",
        "refresh_token": "TG-stored-refresh",
        "user_id": "987654321",
        "public_key": "APP_USR-public-key",
        "live_mode": True,
        "credential_id": GENERATED_CREDENTIAL_ID,
    }
    values.update(overrides)
    return MercadoPagoCredential.create(**values)
