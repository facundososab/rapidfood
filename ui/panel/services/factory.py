"""Single swap point between the mock and the real HTTP client.

Views call get_client() and depend only on the RapidfoodClient interface + DTOs,
so flipping RAPIDFOOD_CLIENT in settings changes the data source without touching
any view or template.
"""
from __future__ import annotations

from functools import lru_cache

from django.conf import settings

from .client import RapidfoodClient


@lru_cache(maxsize=1)
def get_client() -> RapidfoodClient:
    impl = getattr(settings, "RAPIDFOOD_CLIENT", "mock")
    if impl == "http":
        from .http_client import HttpRapidfoodClient

        return HttpRapidfoodClient(
            base_url=settings.RAPIDFOOD_API_BASE_URL,
            token=getattr(settings, "RAPIDFOOD_API_TOKEN", ""),
        )
    from .mock_client import MockRapidfoodClient

    return MockRapidfoodClient()
