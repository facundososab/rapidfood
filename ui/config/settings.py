"""Django settings for the Rapidfood admin panel (presentation layer only).

No domain models, no migrations, no ORM entities for the business domain. Data is
served through panel.services (mock in-memory now, HTTP client later).
"""
import os
from pathlib import Path

BASE_DIR = Path(__file__).resolve().parent.parent

try:
    from dotenv import load_dotenv

    # Local override first (ui/.env), then the repo-root .env (shared with the
    # API and Docker Compose) — first value read wins for each key.
    for env_file in (BASE_DIR / ".env", BASE_DIR.parent / ".env"):
        load_dotenv(env_file)
except Exception:  # python-dotenv optional in sandbox
    pass

SECRET_KEY = os.environ.get("DJANGO_SECRET_KEY", "dev-insecure-rapidfood-panel-key")
DEBUG = os.environ.get("DJANGO_DEBUG", "1") == "1"
ALLOWED_HOSTS = ["*"]

# --- Rapidfood service layer selection --------------------------------------
# "mock" -> in-memory implementation seeded from the Prisma schema.
# "http" -> HttpRapidfoodClient consuming the existing backend API.
# Views/templates depend only on the RapidfoodClient interface + DTOs, so this
# switch is the single swap point.
RAPIDFOOD_CLIENT = os.environ.get("RAPIDFOOD_CLIENT", "mock")
RAPIDFOOD_API_BASE_URL = os.environ.get("RAPIDFOOD_API_BASE_URL", "http://localhost:8000")
RAPIDFOOD_API_TOKEN = os.environ.get("RAPIDFOOD_API_TOKEN", "")

# --- Supabase Auth (staff login) ---------------------------------------------
SUPABASE_URL = os.environ.get("SUPABASE_URL", "")
SUPABASE_ANON_KEY = os.environ.get("SUPABASE_ANON_KEY", "")

LOGIN_URL = "login"
LOGOUT_REDIRECT_URL = "login"

INSTALLED_APPS = [
    "django.contrib.staticfiles",
    "django.contrib.sessions",
    "django.contrib.messages",
    "panel",
]

MIDDLEWARE = [
    "django.middleware.security.SecurityMiddleware",
    "django.contrib.sessions.middleware.SessionMiddleware",
    "django.middleware.common.CommonMiddleware",
    "django.contrib.messages.middleware.MessageMiddleware",
    "panel.middleware.ApiErrorToastMiddleware",
    "panel.middleware.LoginRequiredMiddleware",
    "panel.middleware.ApiSessionTokenMiddleware",
]

# Messages are surfaced as toasts; signed cookies avoid needing a database.
SESSION_ENGINE = "django.contrib.sessions.backends.signed_cookies"

ROOT_URLCONF = "config.urls"

TEMPLATES = [
    {
        "BACKEND": "django.template.backends.django.DjangoTemplates",
        "DIRS": [BASE_DIR / "templates"],
        "APP_DIRS": True,
        "OPTIONS": {
            "context_processors": [
                "django.template.context_processors.request",
                "django.contrib.messages.context_processors.messages",
                "panel.context.nav",
            ],
            "builtins": ["panel.templatetags.rapidfood"],
        },
    },
]

WSGI_APPLICATION = "config.wsgi.application"

# No relational persistence for the domain; the panel is stateless UI over an API.
DATABASES = {}

LANGUAGE_CODE = "es-ar"
TIME_ZONE = "America/Argentina/Buenos_Aires"
USE_I18N = True
USE_TZ = True

STATIC_URL = "static/"
STATICFILES_DIRS = [BASE_DIR / "static"]

DEFAULT_AUTO_FIELD = "django.db.models.BigAutoField"
