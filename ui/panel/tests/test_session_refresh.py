"""Proactive Supabase token renewal (session expiry fix).

Run with the UI settings: DJANGO_SETTINGS_MODULE=config.settings

Supabase access tokens expire (~1h) while the signed-cookie session lives on, so
the panel renews them through GoTrue before they expire. These tests cover the
JWT expiry helper, the renewal middleware, and the failure paths.
"""
import base64
import json
import time

import pytest
from django.conf import settings
from django.test import Client

from panel import auth as panel_auth
from panel import middleware as panel_middleware
from panel.auth import AuthError, get_token_expiry, refresh_access_token

DASHBOARD_URL = "/"


def _b64url(raw: bytes) -> str:
    return base64.urlsafe_b64encode(raw).rstrip(b"=").decode("ascii")


def _handrolled_jwt(exp: float) -> str:
    header = _b64url(b'{"alg":"none","typ":"JWT"}')
    payload = _b64url(json.dumps({"exp": exp}).encode("utf-8"))
    return f"{header}.{payload}.signature"


def _jwt(exp: float) -> str:
    """Build a JWT with the given ``exp`` claim.

    Prefers PyJWT when it is importable (real HS256 token) and otherwise falls
    back to a hand-rolled ``header.payload.signature`` token. Only the payload is
    decoded by the panel — the signature is never verified.
    """
    try:
        import jwt
    except ImportError:
        return _handrolled_jwt(exp)
    return jwt.encode({"exp": exp}, "test-secret-key-with-enough-length-0123456789", algorithm="HS256")


def _authenticated_client(access_token: str, refresh_token: str | None = None) -> Client:
    """Seed a signed-cookie session with the given tokens before the request."""
    client = Client()
    session = client.session
    session["supabase_access_token"] = access_token
    if refresh_token is not None:
        session["supabase_refresh_token"] = refresh_token
    session["supabase_email"] = "staff@rapidfood.local"
    session.save()
    # Signed-cookie sessions are written as a cookie only on a response, so push
    # the freshly signed value onto the client's cookie jar before the request.
    client.cookies[settings.SESSION_COOKIE_NAME] = session.session_key
    return client


def _recording_refresh(monkeypatch, new_pair=("new-access-token", "new-refresh-token")):
    """Patch the middleware's refresher and record the refresh tokens it sees."""
    seen: list[str] = []

    def fake_refresh(refresh_token: str):
        seen.append(refresh_token)
        return new_pair

    monkeypatch.setattr(panel_middleware, "refresh_access_token", fake_refresh)
    return seen


# --- get_token_expiry -------------------------------------------------------

def test_get_token_expiry_reads_the_exp_claim():
    assert get_token_expiry(_jwt(9999999999)) == 9999999999.0


@pytest.mark.parametrize(
    "token",
    [
        "",
        "not-a-jwt",
        "only.two",
        f"header.{_b64url(b'not json')}.signature",
        _b64url(b'{"alg":"none"}') + "." + _b64url(b'{"sub":"no-exp"}') + ".sig",
    ],
)
def test_get_token_expiry_returns_none_for_malformed_tokens(token):
    assert get_token_expiry(token) is None


# --- refresh_access_token (GoTrue grant_type=refresh_token) -----------------

class _FakeResponse:
    def __init__(self, status_code: int, payload: dict):
        self.status_code = status_code
        self._payload = payload

    def json(self):
        return self._payload


def _configure_supabase(monkeypatch):
    monkeypatch.setattr(panel_auth.settings, "SUPABASE_URL", "https://example.supabase.co")
    monkeypatch.setattr(panel_auth.settings, "SUPABASE_ANON_KEY", "anon-key")


def test_refresh_access_token_posts_grant_type_refresh_token(monkeypatch):
    _configure_supabase(monkeypatch)
    calls = {}

    def fake_post(url, **kwargs):
        calls["url"] = url
        calls["json"] = kwargs.get("json")
        calls["headers"] = kwargs.get("headers")
        return _FakeResponse(200, {"access_token": "fresh-access", "refresh_token": "fresh-refresh"})

    monkeypatch.setattr(panel_auth.requests, "post", fake_post)

    assert refresh_access_token("old-refresh") == ("fresh-access", "fresh-refresh")
    assert "grant_type=refresh_token" in calls["url"]
    assert calls["json"] == {"refresh_token": "old-refresh"}
    assert calls["headers"]["apikey"] == "anon-key"


def test_refresh_access_token_raises_when_goTrue_rejects(monkeypatch):
    _configure_supabase(monkeypatch)
    monkeypatch.setattr(
        panel_auth.requests, "post", lambda url, **kwargs: _FakeResponse(401, {"error": "invalid_grant"})
    )

    with pytest.raises(AuthError):
        refresh_access_token("expired-refresh")


def test_refresh_access_token_raises_without_configuration(monkeypatch):
    monkeypatch.setattr(panel_auth.settings, "SUPABASE_URL", "")
    monkeypatch.setattr(panel_auth.settings, "SUPABASE_ANON_KEY", "")

    with pytest.raises(AuthError):
        refresh_access_token("some-refresh")


# --- middleware renewal -----------------------------------------------------

def test_middleware_renews_expired_token_and_stores_new_pair(monkeypatch):
    seen = _recording_refresh(monkeypatch)
    client = _authenticated_client(_jwt(time.time() - 10), refresh_token="old-refresh")

    response = client.get(DASHBOARD_URL)

    assert response.status_code == 200
    assert seen == ["old-refresh"]
    assert client.session["supabase_access_token"] == "new-access-token"
    assert client.session["supabase_refresh_token"] == "new-refresh-token"


def test_middleware_renews_token_inside_the_safety_margin(monkeypatch):
    seen = _recording_refresh(monkeypatch)
    # 200s left is below the 300s margin: renew now rather than die mid-request.
    client = _authenticated_client(_jwt(time.time() + 200), refresh_token="old-refresh")

    client.get(DASHBOARD_URL)

    assert seen == ["old-refresh"]
    assert client.session["supabase_access_token"] == "new-access-token"


def test_middleware_keeps_valid_token_untouched(monkeypatch):
    seen = _recording_refresh(monkeypatch)
    token = _jwt(time.time() + 9999)
    client = _authenticated_client(token, refresh_token="old-refresh")

    response = client.get(DASHBOARD_URL)

    assert response.status_code == 200
    assert seen == []
    assert client.session["supabase_access_token"] == token
    assert client.session["supabase_refresh_token"] == "old-refresh"


def test_middleware_flushes_session_when_refresh_is_rejected(monkeypatch):
    def fake_refresh(refresh_token):
        raise AuthError("refresh token revoked")

    monkeypatch.setattr(panel_middleware, "refresh_access_token", fake_refresh)
    client = _authenticated_client(_jwt(time.time() - 10), refresh_token="old-refresh")

    response = client.get(DASHBOARD_URL)

    # The request still completes; the session is dropped so the login gate
    # redirects on the next request instead of the page crashing.
    assert response.status_code == 200
    assert "supabase_access_token" not in client.session
    assert "supabase_refresh_token" not in client.session

    follow_up = client.get(DASHBOARD_URL)
    assert follow_up.status_code == 302
    assert follow_up.url == "/login/"


def test_middleware_leaves_session_when_no_refresh_token(monkeypatch):
    seen = _recording_refresh(monkeypatch)
    token = _jwt(time.time() - 10)
    client = _authenticated_client(token)  # no refresh token storable

    response = client.get(DASHBOARD_URL)

    assert response.status_code == 200
    assert seen == []
    assert client.session["supabase_access_token"] == token


def test_middleware_ignores_anonymous_requests(monkeypatch):
    seen = _recording_refresh(monkeypatch)
    client = Client()

    response = client.get("/login/")

    assert response.status_code == 200
    assert seen == []
