"""Server-side Supabase (GoTrue) login for the admin panel.

The panel authenticates directly against Supabase Auth (email+password) and
keeps the access token in the signed-cookie session. The staff role/name are
resolved from the backend API (`/api/staff/me/`) when available — gracefully
degrading to just the email otherwise.
"""
from __future__ import annotations

import requests
from django.conf import settings


class AuthError(Exception):
    """Login failed at the Supabase side or Supabase is not configured."""


def login_with_password(email: str, password: str) -> tuple[str, str]:
    """POST GoTrue token endpoint (grant_type=password). Returns (token, email)."""
    base_url = (settings.SUPABASE_URL or "").rstrip("/")
    anon_key = settings.SUPABASE_ANON_KEY or ""
    if not base_url or not anon_key:
        raise AuthError("SUPABASE_URL / SUPABASE_ANON_KEY are not configured")

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
    if response.status_code != 200:
        raise AuthError(
            f"Supabase Auth rejected the login (HTTP {response.status_code})"
        )
    payload = response.json()
    token = payload.get("access_token")
    if not token:
        raise AuthError("Supabase Auth returned no access token")
    user_email = payload.get("user", {}).get("email") or email
    return token, user_email


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