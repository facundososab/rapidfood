"""Turn unexpected API failures on form submits into a toast instead of a 500 page.

The HTTP client raises RuntimeError for API error responses; requests raises its
own exception hierarchy for connection/timeout issues. On a POST we surface the
message as a Django message and send the user back where they came from.
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
        try:
            return self.get_response(request)
        except self._error_types as exc:
            if request.method != "POST":
                raise
            messages.error(request, str(exc) or "No se pudo completar la operación.")
            return redirect(request.META.get("HTTP_REFERER") or "/")
