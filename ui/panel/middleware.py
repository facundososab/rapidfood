"""Turn unexpected API failures on form submits into a toast instead of a 500 page.

The HTTP client raises RuntimeError for API error responses; requests raises its
own exception hierarchy for connection/timeout issues. On a POST we surface the
message as a Django message and send the user back where they came from.

Implemented via the `process_exception` hook (not a try/except around
`get_response`): Django converts view exceptions to responses *before* they
reach `__call__`, so only `process_exception` sees them.
"""
from __future__ import annotations

import time

from django.contrib import messages
from django.shortcuts import redirect

from .auth import AuthError, refresh_access_token
from .services.http_client import ApiAuthError

# Refresh the session token a little before it actually expires.
_REFRESH_SKEW_SECONDS = 30


def _client_error_types() -> tuple[type[BaseException], ...]:
    try:
        import requests
    except ImportError:  # pragma: no cover - mock path has no requests dependency
        return (RuntimeError,)
    return (RuntimeError, requests.exceptions.RequestException)


class ApiErrorToastMiddleware:
    def __init__(self, get_response):
        self.get_response = get_response
        self._error_types = _client_error_types()

    def __call__(self, request):
        return self.get_response(request)

    def process_exception(self, request, exception):
        # The backend rejected the session token (expired/revoked): drop the stale
        # session and send the operator to login, for ANY method. Without this a
        # GET (dashboard) would render a 500 page.
        if isinstance(exception, ApiAuthError):
            request.session.flush()
            return redirect("login")
        if request.method != "POST":
            return None
        if not isinstance(exception, self._error_types):
            return None
        messages.error(request, str(exception) or "No se pudo completar la operación.")
        return redirect(request.META.get("HTTP_REFERER") or "/")


class LoginRequiredMiddleware:
    """Session gate: every page except login/logout/static requires a Supabase token."""

    PUBLIC_PATHS = ("/login/", "/logout/", "/static/")

    def __init__(self, get_response):
        self.get_response = get_response

    def __call__(self, request):
        path = request.path
        if not path.startswith(self.PUBLIC_PATHS):
            if not request.session.get("supabase_access_token"):
                return redirect("login")
        return self.get_response(request)


class ApiSessionTokenMiddleware:
    """Keep the HTTP API client on a valid Supabase token.

    Supabase access tokens expire (~1h). Before the request reaches the view this
    middleware refreshes it with the stored refresh token; if that is impossible
    it clears the session and redirects to login, so an expired session degrades
    to a re-login instead of a 500.
    """

    def __init__(self, get_response):
        self.get_response = get_response

    def __call__(self, request):
        if self._refresh_if_expired(request):
            return redirect("login")
        self._apply_token(request.session.get("supabase_access_token"))
        return self.get_response(request)

    def _refresh_if_expired(self, request) -> bool:
        """Return True when the session was cleared and a re-login is required."""
        session = request.session
        if not session.get("supabase_access_token"):
            return False

        expires_at = session.get("supabase_expires_at")
        if not expires_at or time.time() < (int(expires_at) - _REFRESH_SKEW_SECONDS):
            return False

        refresh_token = session.get("supabase_refresh_token")
        if not refresh_token:
            session.flush()
            return True

        try:
            result = refresh_access_token(refresh_token)
        except AuthError as exc:
            if exc.code == "unreachable":
                # Transient network failure: keep the session and let the API
                # call decide (a real 401 is handled reactively).
                return False
            session.flush()
            return True
        except Exception:
            session.flush()
            return True

        session["supabase_access_token"] = result.access_token
        session["supabase_refresh_token"] = result.refresh_token or refresh_token
        if result.expires_in:
            session["supabase_expires_at"] = int(time.time()) + int(result.expires_in)
        if result.email:
            session["supabase_email"] = result.email
        return False

    def _apply_token(self, token: str | None) -> None:
        try:
            from .services.factory import get_client

            session = getattr(get_client(), "session", None)
        except Exception:  # mock client without a requests session
            return
        if session is None:
            return
        if token:
            session.headers["Authorization"] = f"Bearer {token}"
        else:
            session.headers.pop("Authorization", None)
