# Tasks: scaffold-inicial — Rapidfood shared foundation

## Phase 1: Infrastructure

- [x] 1.1 `uv init --python 3.13`; `pyproject.toml` deps (django>=5.0, djangorestframework>=3.15, prisma>=0.15, psycopg[binary]>=3.2, import-linter>=2.0, pytest>=8.0, pytest-django>=4.8); `uv lock`+`uv sync`.
- [x] 1.2 `.gitignore` (.env, .venv/, __pycache__/, Prisma artifacts).
- [x] 1.3 `docker-compose.yml` (postgres:16, named volume, healthcheck, 5432); `docker compose up -d db`.
- [x] 1.4 `.env.example` (DATABASE_URL, DJANGO_SECRET_KEY, DJANGO_DEBUG, DJANGO_ALLOWED_HOSTS); `cp .env.example .env`.
- [x] 1.5 README.md setup steps (cp .env, docker up, uv sync, prisma generate/migrate dev, runserver, pytest, lint-imports).

## Phase 2: Implementation — Django shell

- [x] 2.1 `manage.py` + `config/{__init__,settings,urls,wsgi,asgi}.py`; INSTALLED_APPS = staticfiles + rest_framework + 5 apps only; sqlite in-memory DATABASES placeholder; Prisma reads DATABASE_URL.
- [x] 2.2 `config/views.py` health → JsonResponse {"status":"ok"}; route `health/` in `config/urls.py`.
- [x] 2.3 `config/db.py` Prisma lazy sync singleton (injected via composition).

## Phase 3: Implementation — Hexagonal app structure

- [x] 3.1 `apps/__init__.py` (real package) + `apps/client` skeleton per design: domain/, application/ports/{inbound,outbound}/, application/use_cases/, adapters/{inbound/http,outbound/prisma}/, composition/ (each a package); empty models.py, views.py, serializers.py, repository, container.
- [x] 3.2 Same: `apps/conversation`.
- [x] 3.3 Same: `apps/order` (+ ports/inbound/__init__.py).
- [x] 3.4 Same: `apps/catalog`.
- [x] 3.5 Same: `apps/config_coupon`.
- [x] 3.6 Verify: `manage.py check` passes; `makemigrations` prints "No changes detected".

## Phase 4: Implementation — Port inventory

- [x] 4.1 `apps/client/application/ports/outbound/client_query_port.py` (ClientDTO; find_by_id, find_by_phone_number).
- [x] 4.2 `apps/client/application/ports/outbound/client_command_port.py` (create).
- [x] 4.3 `apps/catalog/application/ports/outbound/product_query_port.py` (ProductDTO, PriceDTO; find_available_by_id, list_available, find_current_price).
- [x] 4.4 `apps/config_coupon/application/ports/outbound/coupon_query_port.py` (CouponDTO; find_valid_by_code, find_by_id).
- [x] 4.5 `apps/config_coupon/application/ports/outbound/business_config_query_port.py` (BusinessHoursDTO, AddressDTO, BusinessConfigDTO; get_config, is_open_at, is_in_coverage_zone).
- [x] 4.6 `apps/order/application/ports/inbound/order_draft_port.py` (OrderLineDTO, OrderDTO; create_draft, get_draft_by_conversation, add_line, remove_line, set_quantity, apply_coupon, remove_coupon, confirm, abandon) — INBOUND per design.
- [x] 4.7 Verify ports import with zero framework imports (dataclasses + Protocol).

## Phase 5: Implementation — Prisma schema

- [x] 5.1 Root `schema.prisma`: **15 models** + **5 enums** (OrderStatus with **9 states**, DeliveryType, PaymentType, PaymentStatus, WeekDay) per design; sync generator; postgresql datasource; UUID ids; snake @map/@@map; Decimal(10,2)/(5,2); `order.conversationId` nullable FK.
- [x] 5.2 `uv run prisma validate` green.
- [x] 5.3 `uv run prisma generate` (network for engine binaries).
- [x] 5.4 db up + .env: `uv run prisma migrate dev --name init`; commit `prisma/migrations/`.

## Phase 6: Implementation — import-linter

- [x] 6.1 [tool.importlinter] per design: layers (5 apps), http→outbound forbidden, framework ban, per-app sibling forbidden + ignore_imports, acyclic.
- [x] 6.2 `uv run lint-imports` green; adjust ignore_imports from actual output.

## Phase 7: Testing

- [x] 7.1 [tool.pytest.ini_options] (DJANGO_SETTINGS_MODULE=config.settings, pythonpath=["."], testpaths=["tests"], addopts, db marker).
- [x] 7.2 `tests/conftest.py`: prisma_test_db + db session fixtures; ensure test_<db> exists; migrate deploy with test URL; fail fast.
- [x] 7.3 `tests/test_health_smoke.py`: GET /health → 200.
- [x] 7.4 `tests/test_db_smoke.py` (db marker): Prisma create/find_unique/delete roundtrip.
- [x] 7.5 `uv run pytest` green with db up; fast failure without Postgres.

## Phase 8: Documentation & wrap-up

- [x] 8.1 openspec/config.yaml: `strict_tdd: true` + `rules.apply.tdd: true`; remove re-enable note.
- [x] 8.2 README verification pass; fix drift.
- [x] 8.3 Final gate: lint-imports + pytest + manage.py check + makemigrations no-op all green.
