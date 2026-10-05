"""Fernet helpers for the OAuth tokens stored in ``mercadopago_credential``.

The key is ``MERCADOPAGO_TOKEN_ENCRYPTION_KEY`` when set; otherwise it is
derived deterministically from ``DJANGO_SECRET_KEY`` so a deployment does not
need an extra secret just to boot. Tokens are never logged.
"""

from __future__ import annotations

import base64
import hashlib
import os
from functools import lru_cache

from cryptography.fernet import Fernet, InvalidToken

from modules.mercadopago.domain.errors.mercadopago_errors import (
    MercadoPagoConfigurationError,
    MercadoPagoError,
)

ENCRYPTION_KEY_ENV = "MERCADOPAGO_TOKEN_ENCRYPTION_KEY"


def django_secret_key() -> str:
    """Return the project secret used to derive the encryption key."""
    configured = os.environ.get("DJANGO_SECRET_KEY")
    if configured:
        return configured
    # Django is imported lazily: infrastructure owns the framework coupling.
    from django.conf import settings

    return str(settings.SECRET_KEY)


def _fernet_key() -> bytes:
    configured = os.environ.get(ENCRYPTION_KEY_ENV)
    if configured:
        return configured.encode("utf-8")
    digest = hashlib.sha256(django_secret_key().encode("utf-8")).digest()
    return base64.urlsafe_b64encode(digest)


class MercadoPagoTokenCipher:
    """Encrypts and decrypts the Mercado Pago tokens at rest."""

    def __init__(self, key: bytes | str | None = None) -> None:
        try:
            self._fernet = Fernet(key if key is not None else _fernet_key())
        except (TypeError, ValueError) as exc:
            raise MercadoPagoConfigurationError(
                f"{ENCRYPTION_KEY_ENV} is not a valid Fernet key"
            ) from exc

    @classmethod
    def from_env(cls) -> "MercadoPagoTokenCipher":
        return cls()

    def encrypt(self, value: str) -> str:
        return self._fernet.encrypt(value.encode("utf-8")).decode("ascii")

    def decrypt(self, value: str) -> str:
        try:
            return self._fernet.decrypt(value.encode("ascii")).decode("utf-8")
        except (InvalidToken, ValueError, UnicodeError) as exc:
            raise MercadoPagoError(
                "Stored Mercado Pago token could not be decrypted"
            ) from exc


@lru_cache(maxsize=1)
def _default_cipher() -> MercadoPagoTokenCipher:
    return MercadoPagoTokenCipher.from_env()


def encrypt_token(value: str) -> str:
    """Encrypt a token with the deployment key."""
    return _default_cipher().encrypt(value)


def decrypt_token(value: str) -> str:
    """Decrypt a token stored with the deployment key."""
    return _default_cipher().decrypt(value)
