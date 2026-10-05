"""Panel auth tests (Supabase login flow, session gate, logout).

Run with the UI settings: DJANGO_SETTINGS_MODULE=ui.config.settings
"""
import base64
import json

import pytest
from django.test import Client

from panel import auth as panel_auth

PASSWORD_PAYLOAD = {"email": "admin@rapidfood.local", "password": "secret123"}


def _b64url(raw: bytes) -> str:
    return base64.urlsafe_b64encode(raw).rstrip(b"=").decode("ascii")


def _jwt_with_exp(exp: int) -> str:
    """Build an unsigned JWT-shaped token with the given ``exp`` claim.

    The panel base64url-decodes the payload without a signature check, so a
    realistic token is enough here. A far-future ``exp`` keeps the token-refresh
    middleware from attempting a renewal in these login-flow tests.
    """
    header = _b64url(b'{"alg":"none","typ":"JWT"}')
    payload = _b64url(json.dumps({"exp": exp}).encode("utf-8"))
    return f"{header}.{payload}.signature"


ACCESS_TOKEN = _jwt_with_exp(9999999999)


@pytest.fixture()
def mock_login(monkeypatch):
    from panel.views import auth as auth_views

    def _fake(token=ACCESS_TOKEN, email="admin@rapidfood.local",
              refresh_token="refresh-token", profile=None):
        def login(*args, **kwargs):
            return token, email, refresh_token

        monkeypatch.setattr(auth_views, "login_with_password", login)
        monkeypatch.setattr(auth_views, "fetch_staff_profile", lambda t: profile)
        return login

    return _fake


def _reject_login(monkeypatch):
    from panel.views import auth as auth_views

    def login(*args, **kwargs):
        raise panel_auth.AuthError("rejected")

    monkeypatch.setattr(auth_views, "login_with_password", login)
    return login


def test_get_login_page_renders_when_anonymous():
    client = Client()
    response = client.get("/login/")

    assert response.status_code == 200
    assert b"Iniciar sesi" in response.content


def test_login_post_stores_token_and_redirects(mock_login):
    mock_login(profile={"email": "admin@rapidfood.local", "name": "Admin Uno", "role": "ADMIN"})
    client = Client()

    response = client.post("/login/", PASSWORD_PAYLOAD)

    assert response.status_code == 302
    assert response.url == "/"
    session = client.session
    assert session["supabase_access_token"] == ACCESS_TOKEN
    assert session["supabase_refresh_token"] == "refresh-token"
    assert session["supabase_email"] == "admin@rapidfood.local"
    assert session["supabase_staff"]["role"] == "ADMIN"


def test_login_post_rejects_bad_credentials(monkeypatch):
    _reject_login(monkeypatch)
    client = Client()

    response = client.post("/login/", PASSWORD_PAYLOAD)

    assert response.status_code == 200
    assert b"No se pudo iniciar sesi" in response.content


def test_login_post_requires_both_fields():
    client = Client()

    response = client.post("/login/", {"email": "admin@rapidfood.local"})

    assert response.status_code == 200
    assert b"Ingres" in response.content


def test_login_redirects_when_already_logged_in(mock_login):
    mock_login()
    client = Client()
    client.post("/login/", PASSWORD_PAYLOAD)  # real flow: session token set

    response = client.get("/login/")

    assert response.status_code == 302
    assert response.url == "/"


def test_unauthenticated_user_redirected_from_dashboard():
    client = Client()

    response = client.get("/")

    assert response.status_code == 302
    assert response.url == "/login/"


def test_authenticated_user_reaches_dashboard(mock_login):
    mock_login()
    client = Client()
    client.post("/login/", PASSWORD_PAYLOAD)

    response = client.get("/")

    assert response.status_code == 200


def test_logout_clears_session(mock_login):
    mock_login()
    client = Client()
    client.post("/login/", PASSWORD_PAYLOAD)

    response = client.post("/logout/")

    assert response.status_code == 302
    assert response.url == "/login/"
    assert "supabase_access_token" not in client.session


def test_logout_get_clears_session(mock_login):
    """Visiting /logout/ in the browser must actually sign out."""
    mock_login()
    client = Client()
    client.post("/login/", PASSWORD_PAYLOAD)
    assert client.session.get("supabase_access_token")

    response = client.get("/logout/")

    assert response.status_code == 302
    assert response.url == "/login/"
    assert "supabase_access_token" not in client.session


def test_auth_failure_classification():
    """403 counts as an auth failure only for token/credential messages."""
    from panel.services.http_client import _looks_like_auth_failure

    assert _looks_like_auth_failure(401, "anything") is True
    assert _looks_like_auth_failure(403, "Token expired.") is True
    assert _looks_like_auth_failure(403, "Invalid token: bad signature") is True
    assert (
        _looks_like_auth_failure(
            403, "You do not have permission to perform this action."
        )
        is False
    )
    assert _looks_like_auth_failure(500, "Token expired.") is False


def test_expired_token_on_get_redirects_to_login(mock_login, monkeypatch):
    """A 401 from the API on a GET must not render a 500; it re-logs in."""
    from panel.services.http_client import ApiAuthError
    from panel.views import dashboard as dashboard_views

    class RaisingClient:
        def all_orders(self):
            raise ApiAuthError("Token expired.")

    monkeypatch.setattr(dashboard_views, "get_client", lambda: RaisingClient())

    mock_login()
    client = Client()
    client.post("/login/", PASSWORD_PAYLOAD)

    response = client.get("/")

    assert response.status_code == 302
    assert response.url == "/login/"
    assert "supabase_access_token" not in client.session
