"""Shared views (framework-level, not per-app)."""

from django.http import JsonResponse


def health(request) -> JsonResponse:
    """Liveness probe. Never touches the database."""
    return JsonResponse({"status": "ok"})
