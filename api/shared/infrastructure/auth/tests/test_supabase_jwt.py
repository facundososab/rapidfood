"""Unit tests for Supabase JWT authentication (no DB, no network)."""

import datetime
import os

import jwt
import pytest
from django.test import RequestFactory
from rest_framework.exceptions import AuthenticationFailed

from shared.infrastructure.auth.settings import SupabaseAuthSettings
from shared.infrastructure.auth.supabase_jwt import (
    SupabaseJWTAuthentication,
    SupabasePrincipal,
)

TEST_SECRET = "test-supabase-jwt-secret-0123456789abcdef"
TEST_URL = "https://abcdefgh.supabase.co"
TEST_ISSUER = f"{TEST_URL}/auth/v1"


def _sign(payload: dict, secret: str = TEST_SECRET, issuer: str = TEST_ISSUER) -> str:
    claims = {
        "iat": datetime.datetime.now(datetime.timezone.utc),
        "exp": datetime.datetime.now(datetime.timezone.utc) + datetime.timedelta(hours=1),
        "sub": "a1b2c3d4-0000-0000-0000-000000000001",
        "aud": "authenticated",
        "iss": issuer,
        "email": "caja@rapidfood.local",
        "role": "authenticated",
    }
    claims.update(payload)
    return jwt.encode(claims, secret, algorithm="HS256")


@pytest.fixture()
def auth() -> SupabaseJWTAuthentication:
    settings = SupabaseAuthSettings(
        url=TEST_URL,
        anon_key="anon-key",
        jwt_secret=TEST_SECRET,
    )
    return SupabaseJWTAuthentication(settings=settings)


def _request_with(token: str | None) -> object:
    factory = RequestFactory()
    request = factory.get("/api/staff/me/")
    if token is not None:
        request.META["HTTP_AUTHORIZATION"] = f"Bearer {token}"
    return request


def test_valid_token_authenticates_principal(auth: SupabaseJWTAuthentication) -> None:
    token = _sign({})
    request = _request_with(token)

    user, _ = auth.authenticate(request)

    assert isinstance(user, SupabasePrincipal)
    assert user.id == "a1b2c3d4-0000-0000-0000-000000000001"
    assert user.email == "caja@rapidfood.local"
    assert user.is_authenticated is True
    assert user.is_anonymous is False


def test_missing_header_returns_none(auth: SupabaseJWTAuthentication) -> None:
    request = _request_with(None)

    assert auth.authenticate(request) is None


def test_expired_token_rejected(auth: SupabaseJWTAuthentication) -> None:
    token = _sign(
        {"exp": datetime.datetime.now(datetime.timezone.utc) - datetime.timedelta(minutes=1)}
    )

    with pytest.raises(AuthenticationFailed):
        auth.authenticate(_request_with(token))


def test_wrong_secret_rejected() -> None:
    token = _sign({}, secret="another-secret-0123456789abcdefghijklmnop")
    settings = SupabaseAuthSettings(url=TEST_URL, jwt_secret=TEST_SECRET)
    auth = SupabaseJWTAuthentication(settings=settings)

    with pytest.raises(AuthenticationFailed):
        auth.authenticate(_request_with(token))


def test_wrong_audience_rejected(auth: SupabaseJWTAuthentication) -> None:
    token = _sign({"aud": "service_role"})

    with pytest.raises(AuthenticationFailed):
        auth.authenticate(_request_with(token))


def test_wrong_issuer_rejected(auth: SupabaseJWTAuthentication) -> None:
    token = _sign({}, issuer="https://evil.example.com/auth/v1")

    with pytest.raises(AuthenticationFailed):
        auth.authenticate(_request_with(token))


def test_malformed_header_rejected(auth: SupabaseJWTAuthentication) -> None:
    factory = RequestFactory()
    request = factory.get("/api/staff/me/")
    request.META["HTTP_AUTHORIZATION"] = "Bearer"

    with pytest.raises(AuthenticationFailed):
        auth.authenticate(request)


def test_missing_secret_configuration_rejects() -> None:
    token = _sign({})
    settings = SupabaseAuthSettings(url=TEST_URL, jwt_secret=None)
    auth = SupabaseJWTAuthentication(settings=settings)

    with pytest.raises(AuthenticationFailed):
        auth.authenticate(_request_with(token))


def test_settings_from_env() -> None:
    monkeypatch = pytest.MonkeyPatch()
    monkeypatch.setenv("SUPABASE_URL", TEST_URL)
    monkeypatch.setenv("SUPABASE_ANON_KEY", "anon")
    monkeypatch.setenv("SUPABASE_JWT_SECRET", TEST_SECRET)
    monkeypatch.setenv("SUPABASE_SERVICE_ROLE_KEY", "service")

    settings = SupabaseAuthSettings.from_env()

    assert settings.url == TEST_URL
    assert settings.anon_key == "anon"
    assert settings.jwt_secret == TEST_SECRET
    assert settings.service_role_key == "service"
    monkeypatch.undo()


def test_settings_from_env_defaults_empty() -> None:
    monkeypatch = pytest.MonkeyPatch()
    for key in ("SUPABASE_URL", "SUPABASE_ANON_KEY", "SUPABASE_JWT_SECRET", "SUPABASE_SERVICE_ROLE_KEY"):
        monkeypatch.delenv(key, raising=False)

    settings = SupabaseAuthSettings.from_env()

    assert settings.url is None
    assert settings.anon_key is None
    assert settings.jwt_secret is None
    monkeypatch.undo()