"""Server-side Supabase (GoTrue) login for the admin panel.

The panel authenticates directly against Supabase Auth (email+password) and
keeps the access token in the signed-cookie session. The staff role/name are
resolved from the backend API (`/api/staff/me/`) when available — gracefully
degrading to just the email otherwise.

GoTrue access tokens expire (default ~1h). The session therefore also keeps the
``refresh_token`` returned at login so the middleware can silently renew the
access token before it expires (see ``refresh_access_token``).
"""
from __future__ import annotations

import base64
import json

import requests
from django.conf import settings


def _auth_headers(anon_key: str) -> dict[str, str]:
    """Headers GoTrue expects for the token endpoint on this project."""
    return {
        "apikey": anon_key,
        "Authorization": f"Bearer {anon_key}",
        "Content-Type": "application/json",
    }


class AuthError(Exception):
    """Login failed at the Supabase side or Supabase is not configured.

    ``code`` lets the view render a precise, non-leaky message instead of a
    generic one: ``not_configured`` | ``invalid_credentials`` |
    ``email_not_confirmed`` | ``rate_limited`` | ``unreachable`` |
    ``server_error``.
    """

    def __init__(self, message: str, code: str = "server_error") -> None:
        super().__init__(message)
        self.code = code


def _supabase_conf() -> tuple[str, str]:
    """Resolve the GoTrue base URL and anon key, or raise a precise AuthError."""
    base_url = (settings.SUPABASE_URL or "").rstrip("/")
    anon_key = settings.SUPABASE_ANON_KEY or ""
    if not base_url or not anon_key:
        raise AuthError(
            "SUPABASE_URL / SUPABASE_ANON_KEY are not configured",
            code="not_configured",
        )
    return base_url, anon_key


def _failure_code(response) -> str:
    """Map a GoTrue error response to a precise, user-safe failure code."""
    if response.status_code == 429:
        return "rate_limited"
    if response.status_code in (400, 422):
        try:
            error_code = (response.json() or {}).get("error_code", "")
        except ValueError:
            error_code = ""
        if error_code == "email_not_confirmed":
            return "email_not_confirmed"
        return "invalid_credentials"
    return "server_error"


def login_with_password(email: str, password: str) -> tuple[str, str, str]:
    """POST GoTrue token endpoint (grant_type=password).

    Returns ``(access_token, email, refresh_token)``. ``refresh_token`` is empty
    when GoTrue did not return one.
    """
    base_url, anon_key = _supabase_conf()

    try:
        response = requests.post(
            f"{base_url}/auth/v1/token?grant_type=password",
            json={"email": email, "password": password},
            headers=_auth_headers(anon_key),
            timeout=15,
        )
    except requests.RequestException as exc:
        raise AuthError("Supabase Auth is unreachable", code="unreachable") from exc

    if response.status_code != 200:
        raise AuthError(
            f"Supabase Auth rejected the login (HTTP {response.status_code})",
            code=_failure_code(response),
        )

    payload = response.json()
    token = payload.get("access_token")
    if not token:
        raise AuthError("Supabase Auth returned no access token", code="server_error")
    user_email = payload.get("user", {}).get("email") or email
    refresh_token = payload.get("refresh_token") or ""
    return token, user_email, refresh_token


def refresh_access_token(refresh_token: str) -> tuple[str, str]:
    """Exchange a GoTrue refresh token for a fresh ``(access, refresh)`` pair.

    Raises :class:`AuthError` when Supabase is not configured, when no refresh
    token is supplied, or when GoTrue rejects the refresh (expired/revoked
    token). A transport error is reported with ``code="unreachable"`` so the
    caller can tell a rejected refresh apart from a transient network problem.
    """
    base_url, anon_key = _supabase_conf()
    if not refresh_token:
        raise AuthError(
            "No Supabase refresh token available", code="invalid_credentials"
        )

    try:
        response = requests.post(
            f"{base_url}/auth/v1/token?grant_type=refresh_token",
            json={"refresh_token": refresh_token},
            headers=_auth_headers(anon_key),
            timeout=15,
        )
    except requests.RequestException as exc:
        raise AuthError("Supabase Auth is unreachable", code="unreachable") from exc

    if response.status_code != 200:
        raise AuthError(
            f"Supabase Auth rejected the refresh (HTTP {response.status_code})",
            code="invalid_credentials",
        )
    payload = response.json()
    access_token = payload.get("access_token")
    new_refresh_token = payload.get("refresh_token")
    if not access_token or not new_refresh_token:
        raise AuthError(
            "Supabase Auth returned no refreshed tokens", code="server_error"
        )
    return access_token, new_refresh_token


def get_token_expiry(access_token: str) -> float | None:
    """Return the JWT ``exp`` claim (epoch seconds) WITHOUT verifying the signature.

    The panel only needs a best-effort expiry to schedule proactive renewal; it
    never trusts the claim for authorization (the backend API does that). Any
    token that is not a decodable JWT payload with a numeric ``exp`` returns
    ``None``. Doing this by hand keeps PyJWT out of the UI runtime requirements.
    """
    if not isinstance(access_token, str):
        return None
    parts = access_token.split(".")
    if len(parts) != 3:
        return None
    payload_segment = parts[1]
    padding = "=" * (-len(payload_segment) % 4)
    try:
        decoded = base64.urlsafe_b64decode(payload_segment + padding)
        claims = json.loads(decoded)
    except (ValueError, TypeError):
        return None
    if not isinstance(claims, dict):
        return None
    exp = claims.get("exp")
    if exp is None:
        return None
    try:
        return float(exp)
    except (TypeError, ValueError):
        return None


def fetch_staff_profile(token: str) -> dict | None:
    """Best-effort lookup of the staff profile (name/role) from the backend API."""
    base_url = getattr(settings, "RAPIDFOOD_API_BASE_URL", "")
    if not base_url:
        return None
    try:
        response = requests.get(
            f"{base_url.rstrip('/')}/api/staff/me/",
            headers={"Authorization": f"Bearer {token}"},
            timeout=5,
        )
    except requests.RequestException:
        return None
    if response.status_code != 200:
        return None
    data = response.json()
    if not isinstance(data, dict) or "role" not in data:
        return None
    return {"email": data.get("email"), "name": data.get("name"), "role": data.get("role")}
