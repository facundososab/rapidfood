"""Server-side Supabase (GoTrue) login for the admin panel.

The panel authenticates directly against Supabase Auth (email+password) and
keeps the access token in the signed-cookie session. The staff role/name are
resolved from the backend API (`/api/staff/me/`) when available — gracefully
degrading to just the email otherwise.
"""
from __future__ import annotations

from dataclasses import dataclass
from typing import Optional

import requests
from django.conf import settings


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


@dataclass(frozen=True)
class LoginResult:
    """A Supabase token pair plus the operator identity."""

    access_token: str
    email: str
    refresh_token: Optional[str] = None
    expires_in: Optional[int] = None


def _supabase_conf() -> tuple[str, str]:
    base_url = (settings.SUPABASE_URL or "").rstrip("/")
    anon_key = settings.SUPABASE_ANON_KEY or ""
    if not base_url or not anon_key:
        raise AuthError(
            "SUPABASE_URL / SUPABASE_ANON_KEY are not configured",
            code="not_configured",
        )
    return base_url, anon_key


def _to_result(payload: dict, fallback_email: str = "") -> LoginResult:
    token = payload.get("access_token")
    if not token:
        raise AuthError("Supabase Auth returned no access token", code="server_error")
    return LoginResult(
        access_token=token,
        refresh_token=payload.get("refresh_token"),
        email=payload.get("user", {}).get("email") or fallback_email,
        expires_in=payload.get("expires_in"),
    )


def login_with_password(email: str, password: str) -> LoginResult:
    """POST GoTrue token endpoint (grant_type=password)."""
    base_url, anon_key = _supabase_conf()

    try:
        response = requests.post(
            f"{base_url}/auth/v1/token?grant_type=password",
            json={"email": email, "password": password},
            headers={
                "apikey": anon_key,
                "Authorization": f"Bearer {anon_key}",
                "Content-Type": "application/json",
            },
            timeout=15,
        )
    except requests.RequestException as exc:
        raise AuthError("Supabase Auth is unreachable", code="unreachable") from exc

    if response.status_code != 200:
        raise AuthError(
            f"Supabase Auth rejected the login (HTTP {response.status_code})",
            code=_failure_code(response),
        )

    return _to_result(response.json(), fallback_email=email)


def refresh_access_token(refresh_token: str) -> LoginResult:
    """Exchange a refresh token for a fresh access token (grant_type=refresh_token)."""
    base_url, anon_key = _supabase_conf()

    try:
        response = requests.post(
            f"{base_url}/auth/v1/token?grant_type=refresh_token",
            json={"refresh_token": refresh_token},
            headers={
                "apikey": anon_key,
                "Authorization": f"Bearer {anon_key}",
                "Content-Type": "application/json",
            },
            timeout=15,
        )
    except requests.RequestException as exc:
        raise AuthError("Supabase Auth is unreachable", code="unreachable") from exc

    if response.status_code != 200:
        raise AuthError(
            f"Supabase Auth rejected the refresh (HTTP {response.status_code})",
            code="invalid_credentials",
        )

    return _to_result(response.json())


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