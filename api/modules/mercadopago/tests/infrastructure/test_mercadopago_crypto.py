import pytest
from cryptography.fernet import Fernet

from modules.mercadopago.domain.errors.mercadopago_errors import (
    MercadoPagoConfigurationError,
    MercadoPagoError,
)
from modules.mercadopago.infrastructure.adapters.driven.mercadopago import (
    mercadopago_crypto,
)
from modules.mercadopago.infrastructure.adapters.driven.mercadopago.mercadopago_crypto import (
    MercadoPagoTokenCipher,
)


def test_round_trips_a_token_with_an_explicit_key():
    cipher = MercadoPagoTokenCipher(key=Fernet.generate_key())

    encrypted = cipher.encrypt("APP_USR-access-token")

    assert encrypted != "APP_USR-access-token"
    assert cipher.decrypt(encrypted) == "APP_USR-access-token"


def test_derives_the_key_from_the_django_secret(monkeypatch):
    monkeypatch.delenv("MERCADOPAGO_TOKEN_ENCRYPTION_KEY", raising=False)
    monkeypatch.setenv("DJANGO_SECRET_KEY", "project-secret")

    encrypted = MercadoPagoTokenCipher.from_env().encrypt("APP_USR-access-token")

    assert MercadoPagoTokenCipher.from_env().decrypt(encrypted) == "APP_USR-access-token"


def test_a_different_django_secret_cannot_read_the_token(monkeypatch):
    monkeypatch.delenv("MERCADOPAGO_TOKEN_ENCRYPTION_KEY", raising=False)
    monkeypatch.setenv("DJANGO_SECRET_KEY", "project-secret")
    encrypted = MercadoPagoTokenCipher.from_env().encrypt("APP_USR-access-token")

    monkeypatch.setenv("DJANGO_SECRET_KEY", "another-project-secret")

    with pytest.raises(MercadoPagoError, match="could not be decrypted"):
        MercadoPagoTokenCipher.from_env().decrypt(encrypted)


def test_prefers_the_configured_encryption_key(monkeypatch):
    key = Fernet.generate_key()
    monkeypatch.setenv("MERCADOPAGO_TOKEN_ENCRYPTION_KEY", key.decode())

    encrypted = MercadoPagoTokenCipher.from_env().encrypt("APP_USR-access-token")

    assert Fernet(key).decrypt(encrypted.encode("ascii")) == b"APP_USR-access-token"


def test_rejects_an_invalid_configured_key(monkeypatch):
    monkeypatch.setenv("MERCADOPAGO_TOKEN_ENCRYPTION_KEY", "not-a-fernet-key")

    with pytest.raises(MercadoPagoConfigurationError, match="MERCADOPAGO_TOKEN_ENCRYPTION_KEY"):
        MercadoPagoTokenCipher.from_env()


def test_module_helpers_use_the_environment_cipher(monkeypatch):
    monkeypatch.delenv("MERCADOPAGO_TOKEN_ENCRYPTION_KEY", raising=False)
    monkeypatch.setenv("DJANGO_SECRET_KEY", "project-secret")
    mercadopago_crypto._default_cipher.cache_clear()

    try:
        encrypted = mercadopago_crypto.encrypt_token("APP_USR-access-token")

        assert mercadopago_crypto.decrypt_token(encrypted) == "APP_USR-access-token"
    finally:
        mercadopago_crypto._default_cipher.cache_clear()
