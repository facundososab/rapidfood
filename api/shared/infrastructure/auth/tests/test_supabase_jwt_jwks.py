"""Unit tests for JWKS (ES256) mode of the Supabase JWT authentication.

Simulates the Supabase GoTrue JWKS endpoint with an in-memory EC key pair.
No network, no DB.
"""

import datetime

import jwt
import pytest
from cryptography.hazmat.primitives.asymmetric import ec
from cryptography.hazmat.primitives.serialization import Encoding, PublicFormat
from cryptography.hazmat.backends import default_backend
from django.test import RequestFactory
from rest_framework.exceptions import AuthenticationFailed

from shared.infrastructure.auth import supabase_jwt as auth_mod
from shared.infrastructure.auth.settings import SupabaseAuthSettings
from shared.infrastructure.auth.supabase_jwt import (
    SupabaseJWTAuthentication,
    SupabasePrincipal,
)

TEST_URL = "https://abcdefgh.supabase.co"
TEST_ISSUER = f"{TEST_URL}/auth/v1"
TEST_KID = "854a122f-1195-4c3f-bbc0-060b7017396b"

_private_key = ec.generate_private_key(ec.SECP256R1())


def _jwk_dict() -> dict:
    numbers = _private_key.public_key().public_numbers()
    x = numbers.x.to_bytes(32, byteorder="big")
    y = numbers.y.to_bytes(32, byteorder="big")
    import base64

    def b64u(raw: bytes) -> str:
        return base64.urlsafe_b64encode(raw).rstrip(b"=").decode()

    return {
        "kty": "EC",
        "crv": "P-256",
        "kid": TEST_KID,
        "alg": "ES256",
        "use": "sig",
        "x": b64u(x),
        "y": b64u(y),
    }


@pytest.fixture()
def auth() -> SupabaseJWTAuthentication:
    # JWKS mode: url configured, NO jwt_secret
    settings = SupabaseAuthSettings(
        url=TEST_URL,
        anon_key="anon-key",
        jwt_secret=None,
    )
    return SupabaseJWTAuthentication(settings=settings)


@pytest.fixture(autouse=True)
def _fresh_jwks_cache(monkeypatch):
    monkeypatch.setattr(auth_mod, "_jwks_cache", {"ts": 0.0, "data": None})
    yield


@pytest.fixture()
def fake_jwks(monkeypatch, auth):
    def _install(keys):
        payload_data = {"keys": keys}

        def fake_resolve(self):
            auth_mod._jwks_cache["ts"] = 0.0
            return payload_data

        monkeypatch.setattr(auth_mod.SupabaseJWTAuthentication, "_resolve_jwks", fake_resolve)

    return _install


def _sign(payload: dict) -> str:
    claims = {
        "iat": datetime.datetime.now(datetime.timezone.utc),
        "exp": datetime.datetime.now(datetime.timezone.utc) + datetime.timedelta(hours=1),
        "sub": "a1b2c3d4-0000-0000-0000-000000000001",
        "aud": "authenticated",
        "iss": TEST_ISSUER,
        "email": "caja@rapidfood.local",
        "role": "authenticated",
    }
    claims.update(payload)
    return jwt.encode(claims, _private_key, algorithm="ES256", headers={"kid": TEST_KID})


def _request_with(token: str) -> object:
    factory = RequestFactory()
    request = factory.get("/api/staff/me/")
    request.META["HTTP_AUTHORIZATION"] = f"Bearer {token}"
    return request


def test_jwks_valid_es256_token_authenticates(auth, fake_jwks) -> None:
    fake_jwks([_jwk_dict()])

    user, _ = auth.authenticate(_request_with(_sign({})))

    assert isinstance(user, SupabasePrincipal)
    assert user.id == "a1b2c3d4-0000-0000-0000-000000000001"


def test_jwks_unknown_kid_rejected(auth, fake_jwks) -> None:
    fake_jwks([{**_jwk_dict(), "kid": "other-kid"}])

    with pytest.raises(AuthenticationFailed, match="No matching JWKS key"):
        auth.authenticate(_request_with(_sign({})))


def test_jwks_empty_keys_rejected(auth, fake_jwks) -> None:
    fake_jwks([])

    with pytest.raises(AuthenticationFailed):
        auth.authenticate(_request_with(_sign({})))


def test_jwks_expired_token_rejected(auth, fake_jwks) -> None:
    fake_jwks([_jwk_dict()])
    token = _sign(
        {"exp": datetime.datetime.now(datetime.timezone.utc) - datetime.timedelta(minutes=1)}
    )

    with pytest.raises(AuthenticationFailed, match="expired"):
        auth.authenticate(_request_with(token))


def test_jwks_wrong_issuer_rejected(auth, fake_jwks) -> None:
    fake_jwks([_jwk_dict()])
    token = _sign({"iss": "https://evil.example.com/auth/v1"})

    with pytest.raises(AuthenticationFailed, match="issuer"):
        auth.authenticate(_request_with(token))


def test_missing_url_and_secret_rejected() -> None:
    auth = SupabaseJWTAuthentication(settings=SupabaseAuthSettings())

    with pytest.raises(AuthenticationFailed, match="not configured"):
        auth.authenticate(_request_with(_sign({})))


def test_network_failure_is_authentication_failure(monkeypatch, auth) -> None:
    def boom(self):
        raise AuthenticationFailed("Could not fetch Supabase JWKS")

    monkeypatch.setattr(auth_mod.SupabaseJWTAuthentication, "_resolve_jwks", boom)

    with pytest.raises(AuthenticationFailed, match="JWKS"):
        auth.authenticate(_request_with(_sign({})))