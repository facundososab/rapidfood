"""DjangoStateSigner — signs and validates the OAuth ``state`` parameter.

The payload is ``{"business_config_id": ..., "ts": <epoch seconds>,
"code_verifier": <str | None>}`` signed with ``django.core.signing.Signer``. The
signature protects against tampering; ``ts`` bounds the lifetime of a state so a
leaked callback URL cannot be replayed later. The PKCE verifier travels inside
the state because the callback runs in a different request than the one that
generated it. Django never leaks into the domain or application layers: this
adapter implements the driven port.
"""

from __future__ import annotations

import json
import time
from collections.abc import Callable

from django.core.signing import Signer

from modules.mercadopago.application.ports.driven.mercadopago_state_signer import (
    SignedState,
)
from modules.mercadopago.domain.errors.mercadopago_errors import MercadoPagoStateError
from modules.mercadopago.infrastructure.adapters.driven.mercadopago.mercadopago_crypto import (
    django_secret_key,
)

DEFAULT_STATE_MAX_AGE_SECONDS = 600
STATE_SALT = "modules.mercadopago.oauth.state"


class DjangoStateSigner:
    def __init__(
        self,
        key: str | None = None,
        max_age_seconds: int = DEFAULT_STATE_MAX_AGE_SECONDS,
        clock: Callable[[], float] | None = None,
    ) -> None:
        self._signer = Signer(key=key or django_secret_key(), salt=STATE_SALT)
        self._max_age_seconds = max_age_seconds
        self._clock = clock if clock is not None else time.time

    def sign(self, business_config_id: str, code_verifier: str | None = None) -> str:
        payload = json.dumps(
            {
                "business_config_id": business_config_id,
                "ts": int(self._clock()),
                "code_verifier": code_verifier,
            }
        )
        return self._signer.sign(payload)

    def unsign(self, state: str) -> SignedState:
        business_config_id, issued_at, code_verifier = self._read(state)

        if not isinstance(business_config_id, str) or not business_config_id.strip():
            raise MercadoPagoStateError("Mercado Pago OAuth state is invalid")

        if code_verifier is not None and not isinstance(code_verifier, str):
            raise MercadoPagoStateError("Mercado Pago OAuth state is invalid")

        if self._clock() - issued_at > self._max_age_seconds:
            raise MercadoPagoStateError("Mercado Pago OAuth state has expired")

        return SignedState(
            business_config_id=business_config_id.strip(),
            code_verifier=code_verifier,
        )

    def _read(self, state: str) -> tuple[object, int, object]:
        try:
            payload = self._signer.unsign(state)
            data = json.loads(payload)
            return data["business_config_id"], int(data["ts"]), data.get("code_verifier")
        except Exception as exc:
            raise MercadoPagoStateError("Mercado Pago OAuth state is invalid") from exc
