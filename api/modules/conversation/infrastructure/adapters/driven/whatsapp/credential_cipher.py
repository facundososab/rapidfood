"""Symmetric encryption for WhatsApp secrets at rest (infrastructure concern).

The access token and app secret are encrypted with Fernet before they touch the
database and decrypted on read, so they never persist in plaintext. The key comes
from ``WHATSAPP_CONFIG_ENCRYPTION_KEY`` (a valid Fernet key); when it is absent it
is derived from ``DJANGO_SECRET_KEY`` as a DEV fallback — rotating the Django
secret then invalidates stored secrets, so set the dedicated key in production.
"""
from __future__ import annotations

import base64
import hashlib
import logging

logger = logging.getLogger(__name__)


def _fernet():
    from cryptography.fernet import Fernet
    from django.conf import settings

    key = (getattr(settings, "WHATSAPP_CONFIG_ENCRYPTION_KEY", "") or "").strip()
    if key:
        return Fernet(key.encode())

    secret = getattr(settings, "SECRET_KEY", "dev-only-insecure-key")
    logger.warning(
        "WHATSAPP_CONFIG_ENCRYPTION_KEY is not set; deriving the WhatsApp secrets "
        "key from DJANGO_SECRET_KEY (dev fallback)."
    )
    derived = base64.urlsafe_b64encode(hashlib.sha256(secret.encode()).digest())
    return Fernet(derived)


class CredentialCipher:
    def encrypt(self, value: str | None) -> str | None:
        if value is None:
            return None
        return _fernet().encrypt(value.encode("utf-8")).decode("ascii")

    def decrypt(self, token: str | None) -> str | None:
        if token is None:
            return None
        return _fernet().decrypt(token.encode("ascii")).decode("utf-8")
