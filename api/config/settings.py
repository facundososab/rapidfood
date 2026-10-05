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
    "modules.business",
    "modules.staff",
    "modules.mercadopago",
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
    # Staff-only by default: every view requires a valid Supabase JWT unless it
    # opts out with AllowAny (public: health probe, MP webhook, payment links,
    # conversation/bot endpoints).
    "DEFAULT_PERMISSION_CLASSES": ["rest_framework.permissions.IsAuthenticated"],
    "DEFAULT_AUTHENTICATION_CLASSES": [
        "shared.infrastructure.auth.supabase_jwt.SupabaseJWTAuthentication"
    ],
    # No sessions → CSRF not enforced; JWT auth only.
    "UNAUTHENTICATED_USER": None,
}

# DRF's browsable API needs Django's template machinery to render its error
# pages (e.g. rest_framework/api.html) when a request fails in DEBUG mode.
TEMPLATES = [
    {
        "BACKEND": "django.template.backends.django.DjangoTemplates",
        "DIRS": [],
        "APP_DIRS": True,  # DRF ships its own templates inside the package
        "OPTIONS": {
            "context_processors": [],
        },
    },
]

# Delivery module — OpenRouteService API key (required for geocoding/routing).
OPENROUTESERVICE_API_KEY: str = os.environ.get("OPENROUTESERVICE_API_KEY", "")

# Conversation agent — LangGraph runtime. The provider is swappable behind the
# agent runner port; `AGENT_PROVIDER` selects it explicitly ("groq" | "gemini"),
# or "auto" infers it from the model name (gemini-* -> Gemini, otherwise Groq).
GROQ_API_KEY: str = os.environ.get("GROQ_API_KEY", "")
GEMINI_API_KEY: str = os.environ.get("GEMINI_API_KEY", "")
AGENT_PROVIDER: str = os.environ.get("AGENT_PROVIDER", "auto")
AGENT_MODEL: str = os.environ.get(
    "AGENT_MODEL",
    "llama-3.3-70b-versatile",
)
# DEV FALLBACK ONLY, and optional: the definitive multi-tenant design resolves
# the business from the channel/runtime context. When this is empty (or "default")
# the single existing business is resolved dynamically, which survives database
# re-seeds (the business row id is a generated UUID).
AGENT_BUSINESS_CONFIG_ID: str = os.environ.get("AGENT_BUSINESS_CONFIG_ID", "")

# WhatsApp Cloud API. Credentials are stored PER BUSINESS in the database and
# edited from the admin panel, so there is no token/phone id here. The only
# setting is the Fernet key that encrypts the per-business secrets at rest.
# Generate one with:
#   python -c "from cryptography.fernet import Fernet; print(Fernet.generate_key().decode())"
# When empty, a key is derived from DJANGO_SECRET_KEY (dev fallback only).
WHATSAPP_CONFIG_ENCRYPTION_KEY: str = os.environ.get(
    "WHATSAPP_CONFIG_ENCRYPTION_KEY", ""
)
# Speech-to-text model for inbound WhatsApp voice notes. Reuses GEMINI_API_KEY /
# GROQ_API_KEY. Empty = provider default (Gemini -> AGENT_MODEL, Groq -> a Whisper
# model). Without any key, audio messages get a friendly fallback reply.
WHATSAPP_TRANSCRIPTION_MODEL: str = os.environ.get(
    "WHATSAPP_TRANSCRIPTION_MODEL", ""
)

# LangSmith tracing (LANGSMITH_TRACING / LANGSMITH_API_KEY / LANGSMITH_PROJECT /
# LANGSMITH_WORKSPACE_ID / LANGSMITH_ENDPOINT) is NOT copied into Django
# settings on purpose: the LangChain/LangSmith client reads os.environ directly,
# and the .env loader above has already populated it. Keeping a second copy here
# would only create drift.
