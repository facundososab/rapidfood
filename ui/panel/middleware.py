"""Turn unexpected API failures on form submits into a toast instead of a 500 page.

The HTTP client raises RuntimeError for API error responses; requests raises its
own exception hierarchy for connection/timeout issues. On a POST we surface the
message as a Django message and send the user back where they came from.

Implemented via the `process_exception` hook (not a try/except around
`get_response`): Django converts view exceptions to responses *before* they
reach `__call__`, so only `process_exception` sees them.
"""
from __future__ import annotations

from django.contrib import messages
from django.shortcuts import redirect


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
    """

    def __init__(self, get_response):
        self.get_response = get_response

    def __call__(self, request):
        self._apply_token(request.session.get("supabase_access_token"))
        return self.get_response(request)

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
