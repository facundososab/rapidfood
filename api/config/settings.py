"""Django settings — Rapidfood.

Django is ONLY the inbound HTTP shell. Prisma Client Python owns the entire
data layer (single source of truth: ``schema.prisma``). Therefore:

- INSTALLED_APPS is minimal: staticfiles + DRF + the 5 hexagonal apps.
  No auth, no sessions, no admin — zero Django-owned tables.
- DATABASES is a minimal sqlite in-memory placeholder so Django/pytest-django
  machinery runs WITHOUT touching the Prisma-owned Postgres. Prisma alone
  reads ``DATABASE_URL``.
"""

import os
from pathlib import Path

BASE_DIR = Path(__file__).resolve().parents[2]


def _load_dotenv() -> None:
    """Minimal .env loader (no third-party deps).

    The Prisma CLI loads ``.env`` natively, but the Prisma Python client reads
    ``os.environ`` at ``connect()`` time — so the repo-root ``.env`` (and any
    local ``api/.env`` override) is loaded here, before any settings are read,
    in every Django context (runserver, manage.py, pytest-django).
    """
    for env_file in (BASE_DIR / ".env", BASE_DIR.parent / ".env"):
        if not env_file.exists():
            continue
        for line in env_file.read_text(encoding="utf-8").splitlines():
            line = line.strip()
            if not line or line.startswith("#") or "=" not in line:
                continue
            key, _, value = line.partition("=")
            key = key.strip()
            value = value.strip()
            if (value.startswith('"') and value.endswith('"')) or (
                value.startswith("'") and value.endswith("'")
            ):
                value = value[1:-1]
            if key and key not in os.environ:
                os.environ[key] = value


_load_dotenv()

SECRET_KEY = os.environ.get("DJANGO_SECRET_KEY", "dev-only-insecure-key")
DEBUG = os.environ.get("DJANGO_DEBUG", "1") == "1"
ALLOWED_HOSTS = os.environ.get("DJANGO_ALLOWED_HOSTS", "*").split(",")

INSTALLED_APPS = [
    "django.contrib.staticfiles",
    "rest_framework",
    "modules.client",
    "modules.conversation",
    "modules.order",
    "modules.catalog",
    "modules.config_coupon",
    "modules.delivery",
]

# Placeholder only: lets Django/pytest-django run without owning Postgres.
# Real data access happens through Prisma (DATABASE_URL), never Django ORM.
DATABASES = {
    "default": {
        "ENGINE": "django.db.backends.sqlite3",
        "NAME": ":memory:",
    }
}

ROOT_URLCONF = "config.urls"

WSGI_APPLICATION = "config.wsgi.application"
ASGI_APPLICATION = "config.asgi.application"
STATIC_URL = "static/"

# No sessions/auth/admin → nothing to process.
MIDDLEWARE: list[str] = []

REST_FRAMEWORK = {
    "DEFAULT_PERMISSION_CLASSES": ["rest_framework.permissions.AllowAny"],
    # No sessions → CSRF not enforced; token auth later if needed (design).
    "DEFAULT_AUTHENTICATION_CLASSES": [],
    "UNAUTHENTICATED_USER": None,
}

# Delivery module — OpenRouteService API key (required for geocoding/routing).
OPENROUTESERVICE_API_KEY: str = os.environ.get("OPENROUTESERVICE_API_KEY", "")
