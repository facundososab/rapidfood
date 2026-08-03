# Delta for Scaffold

## Purpose

Shared foundation for rapidfood: a uv-managed Django 5 + DRF HTTP shell where Prisma Client Python owns all persistence, five empty hexagonal apps with port contracts, Postgres 16 via Docker, import-linter enforcement, and pytest infrastructure. Business logic ships in later changes.

## ADDED Requirements

### Requirement: Project Setup

The scaffold MUST be a uv-managed project (pyproject.toml, uv.lock) on Python 3.13 declaring: django, djangorestframework, prisma, psycopg[binary], import-linter, pytest, pytest-django. It MUST include docker-compose.yml (Postgres 16, named volume, healthcheck), .env.example with DATABASE_URL, .gitignore, and a README with setup steps.

#### Scenario: Clean-clone setup works

- GIVEN a fresh clone and running Docker
- WHEN the developer follows README: uv sync, uv run prisma generate, docker compose up -d, uv run prisma migrate dev
- THEN uv run django check passes

#### Scenario: Offline install

- GIVEN no network access
- WHEN uv sync runs
- THEN it fails on the Prisma engine download; README documents network as a prerequisite

### Requirement: Django Shell

The scaffold MUST ship manage.py and config/ (settings, urls, wsgi/asgi). urls.py MUST route GET /health to a view returning 200 with status. INSTALLED_APPS MUST contain only the five apps plus rest_framework (staticfiles MAY be included) and MUST NOT include auth, sessions, or admin. DATABASES MUST be a minimal sqlite in-memory placeholder so Django/pytest-django machinery runs WITHOUT touching Postgres; Prisma alone reads DATABASE_URL.

#### Scenario: Health endpoint

- GIVEN the server is running
- WHEN a client GETs /health
- THEN the response is 200

#### Scenario: Django migration no-op

- GIVEN empty models.py across all apps
- WHEN uv run python manage.py makemigrations runs
- THEN it reports no changes; Prisma owns all tables

### Requirement: Hexagonal App Structure

apps/ MUST be a real package containing client, conversation, order, catalog, config_coupon. Each app MUST contain domain/, application/ports/inbound/, application/ports/outbound/, application/use_cases/, adapters/inbound/, adapters/outbound/, composition/, each a package with __init__.py (.gitkeep where needed). models.py MUST remain empty.

#### Scenario: Apps import cleanly

- GIVEN the scaffold installed
- WHEN Django loads INSTALLED_APPS
- THEN all five apps import without error

### Requirement: Port Inventory

Each outbound port MUST be a Protocol in its owning app's application/ports/outbound/, contract-only, no implementation:

| Port | Owner |
|---|---|
| ClientQueryPort, ClientCommandPort | client |
| ProductQueryPort | catalog |
| CouponQueryPort, BusinessConfigQueryPort | config_coupon |
| OrderDraftPort (create/addLine/removeLine/setQuantity/applyCoupon/confirm/abandon) | order |

Consumer apps MUST import only the Protocol, never adapter or framework types.

#### Scenario: Cross-app port consumption

- GIVEN conversation needs draft ordering
- WHEN it imports apps.order.application.ports.outbound.OrderDraftPort
- THEN the import resolves and requires no adapter or framework

### Requirement: Prisma Data Model

A single root schema.prisma (datasource postgresql; generator interface = "sync") MUST define all 16 entities: businessConfiguration, businessHours, address, client, conversation, message, order, orderLine, product, price, category, discount, coupon, appliedCoupon, payment. Ids MUST be UUID strings. Enums MUST be limited to fixed vocabulary (OrderStatus, DeliveryType, PaymentType, PaymentStatus; open vocab stays String). Money MUST be Decimal(10,2) (discount.percentage Decimal(5,2)). orderLine MUST snapshot unitPrice (RN-024/035); appliedCoupon MUST copy coupon fields (RN-033/034); order.addressId MUST be nullable until confirm (RN-020). Fields/tables MUST be snake_case via @map/@@map. Initial prisma/migrations/ MUST be committed.

#### Scenario: Schema validates

- GIVEN the schema file
- WHEN uv run prisma validate runs
- THEN it passes and all 16 entities are defined

#### Scenario: SQL naming

- GIVEN camelCase Prisma fields
- WHEN the generated migration SQL is inspected
- THEN tables and columns are snake_case

### Requirement: Architecture Contracts

[tool.importlinter] MUST define: (1) layers per app (adapters → application → domain); (2) forbidden django/rest_framework/prisma imports from apps.*.domain and apps.*.application.use_cases; (3) forbidden cross-app imports except via application.ports (whitelisted ignore_imports). uv run lint-imports MUST pass.

#### Scenario: Framework ban enforced

- GIVEN a use case imports prisma
- WHEN uv run lint-imports runs
- THEN the forbidden contract fails, naming the import

#### Scenario: Port-only cross-app edge

- GIVEN order imports apps.client.application.ports (whitelisted) and separately apps.client.adapters (not)
- WHEN uv run lint-imports runs
- THEN the port edge passes and the adapter edge fails

### Requirement: Test Infrastructure

pytest and pytest-django MUST be configured (DJANGO_SETTINGS_MODULE=config.settings). Tests MUST target a dedicated Postgres test database via DATABASE_URL. tests/conftest.py MUST provide a session-scoped fixture running prisma migrate deploy against that database — Django's runner creates test_<db> but never Prisma tables. A smoke test MUST write/read via Prisma. After pytest lands, testing.strict_tdd in openspec/config.yaml MUST be re-enabled (currently false).

#### Scenario: Test DB has Prisma tables

- GIVEN pytest starts against a Postgres test database
- WHEN the session fixture runs prisma migrate deploy
- THEN Prisma tables exist and the smoke test passes

#### Scenario: Fixture fails fast without Postgres

- GIVEN Postgres is unreachable
- WHEN pytest runs
- THEN the session fixture errors quickly with a connection error
