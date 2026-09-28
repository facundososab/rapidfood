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

import requests
from django.contrib import messages
from django.shortcuts import redirect

from .auth import AuthError, get_token_expiry, refresh_access_token

# Renew the Supabase access token once it has this little time left, so a page
# that loads slowly (or an image/partial fetched late) never crosses the expiry
# mid-request and dies with the backend's `Token expired.` RuntimeError.
REFRESH_MARGIN_SECONDS = 300


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
    """Forward the logged-in Supabase token to the HTTP API client.

    The panel uses a singleton HTTP client (``get_client()``); this middleware
    refreshes its Authorization header from the session on every request so the
    API receives the operator JWT. Single-user panel: the header reflects the
    last active session.

    Supabase access tokens expire (default ~1h). Before applying the token, the
    middleware transparently renews it through GoTrue when it is expired or
    about to expire, storing the fresh pair back in the session.
    """

    def __init__(self, get_response):
        self.get_response = get_response

    def __call__(self, request):
        token = self._renew_expired_access_token(request)
        if token is None:
            token = request.session.get("supabase_access_token")
        self._apply_token(token)
        return self.get_response(request)

    def _renew_expired_access_token(self, request) -> str | None:
        """Renew the session's access token when needed; never raises.

        Returns the fresh access token when a renewal happened, or ``None`` when
        there was nothing to do (anonymous, still valid, no refresh token) or
        the session was dropped.
        """
        access_token = request.session.get("supabase_access_token")
        if not access_token:
            return None  # anonymous request: nothing to renew

        expiry = get_token_expiry(access_token)
        if expiry is not None and expiry - time.time() > REFRESH_MARGIN_SECONDS:
            return None  # still comfortably valid

        # Expired, near expiry, or an undecodable token: try to renew.
        refresh_token = request.session.get("supabase_refresh_token")
        if not refresh_token:
            # No way to renew: leave the session untouched and let the API reject
            # the stale token (the error-toast middleware surfaces it).
            return None

        try:
            new_access_token, new_refresh_token = refresh_access_token(refresh_token)
        except AuthError:
            # Refresh token expired/revoked: drop the session so the login gate
            # redirects on the next request instead of crashing the page.
            request.session.flush()
            return None
        except requests.RequestException:
            # Transient network/timeout failure: keep the session and let the
            # API surface the stale token rather than raising a 500 here.
            return None

        request.session["supabase_access_token"] = new_access_token
        request.session["supabase_refresh_token"] = new_refresh_token
        request.session.modified = True
        return new_access_token

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
