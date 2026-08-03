# Verify Report — scaffold-inicial

- **Change**: scaffold-inicial
- **Mode**: openspec (filesystem artifacts)
- **Date**: 2026-08-03
- **Verifier**: sdd-verify executor
- **Verdict**: **PASS WITH WARNINGS** (all 7 ADDED requirements met, all gates green, 23/23 tasks complete)
- **Blocking for archive**: 1 CRITICAL process finding (missing apply-progress.md / TDD Cycle Evidence) — see Issues

## 1. Requirements verified (spec → code)

### Req: Project Setup — ✅ PASS
| Spec | Implementation | Status |
|---|---|---|
| uv-managed project, pyproject.toml + uv.lock, Python 3.13 | `pyproject.toml` + `uv.lock` present; requires-python >=3.13; `uv run` works (all commands executed via uv) | ✅ |
| deps: django, djangorestframework, prisma, psycopg[binary], import-linter, pytest, pytest-django | All declared: `django>=5.0`, `djangorestframework>=3.15`, `prisma>=0.15`, `psycopg[binary]>=3.2` (main); `import-linter>=2.0`, `pytest>=8.0`, `pytest-django>=4.8` (dev) | ✅ |
| docker-compose.yml (Postgres 16, named volume, healthcheck) | `docker-compose.yml`: postgres:16-alpine, named volume `pgdata`, `pg_isready` healthcheck, 5432; `rapidfood_db` **Up (healthy)** | ✅ |
| .env.example with DATABASE_URL | `.env.example` lines 1–8: DATABASE_URL, DJANGO_SECRET_KEY, DJANGO_DEBUG, DJANGO_ALLOWED_HOSTS, POSTGRES_* | ✅ |
| .gitignore | `.env`, `.venv/`, `__pycache__/`, Prisma artifacts (`.prisma/`, `*.pyc`) | ✅ |
| README with setup steps | README: `cp .env.example .env`, `docker compose up -d db`, `uv sync`, `uv run prisma generate`, `uv run prisma migrate dev`, `runserver`, `pytest`, `lint-imports`; **documents network as prerequisite** (Offline scenario) | ✅ |

**Scenario "Clean-clone setup works"**: each constituent step verified individually (uv sync ✅, prisma generate ✅ — generated client is imported by passing tests, prisma validate ✅, docker compose up ✅ healthy, prisma migrate deploy ✅ run inside pytest session fixture, `manage.py check` ✅). Full clean-clone replay not executed (requires fresh clone), but no step is unproven.
**Scenario "Offline install"**: README documents network requirement (verified in text). ✅

### Req: Django Shell — ✅ PASS
| Spec | Implementation | Status |
|---|---|---|
| manage.py + config/{settings,urls,wsgi,asgi} | All present (`manage.py`, `config/__init__.py`, `config/settings.py`, `config/urls.py`, `config/wsgi.py`, `config/asgi.py`) | ✅ |
| /health → 200 with status | `config/urls.py`: `path("health/", views.health, name="health")`; `config/views.py`: `health` → `JsonResponse({"status": "ok"})`; test asserts 200 + `{"status": "ok"}` | ✅ |
| INSTALLED_APPS = 5 apps + rest_framework (+staticfiles), NO auth/sessions/admin | `staticfiles` + `rest_framework` + client/conversation/order/catalog/config_coupon — no auth, no sessions, no admin | ✅ |
| DATABASES minimal sqlite in-memory placeholder; Prisma alone reads DATABASE_URL | `sqlite3` + `":memory:"`; `config/db.py` `Database` class reads `DATABASE_URL` env for Prisma | ✅ |

**Scenario "Health endpoint"**: `test_health_smoke.py` → GET /health → 200, json `{"status":"ok"}`. ✅
**Scenario "Django migration no-op"**: `uv run python manage.py makemigrations --check --dry-run` → "No changes detected". ✅

### Req: Hexagonal App Structure — ✅ PASS
| Spec | Implementation | Status |
|---|---|---|
| apps/ real package with 5 subapps | `apps/__init__.py` present; `apps/client|conversation|order|catalog|config_coupon` all present with `__init__.py` | ✅ |
| Per app: domain/, application/ports/{inbound,outbound}/, application/use_cases/, adapters/inbound/, adapters/outbound/, composition/, each a package | Verified for all 5 apps: `domain/`, `application/ports/inbound/`, `application/ports/outbound/`, `application/use_cases/`, `adapters/inbound/http/`, `adapters/outbound/prisma/`, `composition/` — all with `__init__.py` (e.g. `apps/order/application/ports/inbound/__init__.py` per task 3.3) | ✅ |
| models.py empty | `models.py` empty in all 5 apps | ✅ |
| apps.py AppConfig | Each app has `apps.py` with AppConfig (ClientConfig, ConversationConfig, OrderConfig, CatalogConfig, Config_couponConfig) | ✅ |

**Scenario "Apps import cleanly"**: `manage.py check` passes (loads all INSTALLED_APPS); all 5 apps importable. ✅

### Req: Port Inventory — ✅ PASS (superset of spec ops)
| Port | Spec ops | Impl ops | Status |
|---|---|---|---|
| ClientQueryPort (client) | — | `find_by_id`, `find_by_phone_number` | ✅ |
| ClientCommandPort (client) | — | `create` | ✅ |
| ProductQueryPort (catalog) | — | `find_available_by_id`, `list_available`, `find_current_price` | ✅ |
| CouponQueryPort (config_coupon) | — | `find_valid_by_code`, `find_by_id` | ✅ |
| BusinessConfigQueryPort (config_coupon) | — | `get_config`, `is_open_at`, `is_in_coverage_zone` | ✅ |
| OrderDraftPort (order) | create/addLine/removeLine/setQuantity/applyCoupon/confirm/abandon | `create_draft`, `get_draft_by_conversation`, `add_line`, `remove_line`, `set_quantity`, `apply_coupon`, `remove_coupon`, `confirm`, `abandon` | ✅ |

- All ports are `typing.Protocol`s with frozen DTOs, contract-only, zero framework imports (verified by read + task 4.7).
- Cross-app import of protocols resolves: `uv run python -c "from apps.order.application.ports.inbound.order_draft_port import OrderDraftPort; from apps.client.application.ports.outbound.client_query_port import ClientQueryPort"` ✅

**Scenario "Cross-app port consumption"**: port import resolves with no adapter/framework (negative-gate verified, see §4). ⚠️ NOTE: scenario text says `application.ports.outbound.OrderDraftPort`; design.md + implementation intentionally use `application/ports/inbound/` (OrderDraftPort is the inbound contract the conversation agent calls). Intent satisfied; spec text drift flagged in Issues.

### Req: Prisma Data Model — ✅ PASS (15 entities per design; see WARNING)
| Spec | Implementation | Status |
|---|---|---|
| Single root schema.prisma, datasource postgresql, generator interface "sync" | Root `schema.prisma`; `provider = "postgresql"`; `interface = "sync"` | ✅ |
| All entities defined | **15 models** (design corrected upstream "16": businessConfiguration, businessHours, address, client, conversation, message, order, orderLine, product, price, category, discount, coupon, appliedCoupon, payment) | ✅* |
| UUID string ids | `String @id @default(uuid()) @db.Uuid` on all 15 models | ✅ |
| Enums limited to fixed vocabulary | 5 enums: OrderStatus (**9 states** incl. BORRADOR per RN-001), DeliveryType, PaymentType, PaymentStatus, WeekDay | ✅ |
| Money Decimal(10,2); discount.percentage Decimal(5,2) | Verified in schema | ✅ |
| orderLine snapshots unitPrice (RN-024/035) | `unitPrice Decimal @db.Decimal(10,2)` nullable (NULL in BORRADOR, frozen at confirm) | ✅ |
| appliedCoupon copies coupon fields (RN-033/034) | `discountPercentage` + `discountAmount` snapshot fields | ✅ |
| order.addressId nullable until confirm (RN-020) | `addressId String?` + `clientId String?` nullable FK | ✅ |
| order.conversationId nullable FK (RN-030/031, replaces conversation.draftOrderId) | `conversationId String? @db.Uuid`; relation on conversation | ✅ |
| snake_case via @map/@@map | All tables/columns snake_case in schema and migration SQL | ✅ |
| Initial prisma/migrations/ committed | Migration committed at **`migrations/20260803222839_init/migration.sql`** + `migration_lock.toml` (root `migrations/` — see WARNING re: `prisma/migrations/` path in spec) | ✅* |

\* spec text says "16 entities" and scenario says "all 16 entities are defined" but the spec's own entity list enumerates exactly 15; design.md documents the correction to 15 (class diagram has 15 classes). Implementation matches design. See Issues.

**Scenario "Schema validates"**: `uv run prisma validate` → "The schema at schema.prisma is valid 🚀", exit 0. ✅
**Scenario "SQL naming"**: migration SQL inspected — snake_case tables/columns (e.g. `business_configuration`, `client`, `conversation`, `orderLine` → `order_line`, `message`...). ✅

### Req: Architecture Contracts — ✅ PASS
| Spec | Implementation | Status |
|---|---|---|
| (1) layers per app (adapters → application → domain) | Per-app "Hexagonal layers" contracts (9 contracts total: 5× layers, 1× http→outbound forbidden, 1× framework ban, per-app siblings-port whitelists) | ✅ |
| (2) forbidden django/rest_framework/prisma from domain + use_cases | "Domain, ports and use cases must not import frameworks" contract | ✅ |
| (3) forbidden cross-app imports except via application.ports | Per-app sibling contracts with `ignore_imports` whitelisting `application.ports` | ✅ |
| `uv run lint-imports` passes | **9 contracts KEPT, 0 broken**, exit 0 (117 files, 23 deps); warnings are expected unmatched whitelist entries per `unmatched_ignore_imports_alerting = "warn"` | ✅ |

**Scenario "Framework ban enforced"**: negative-gate verified — a use case importing prisma broke the contract naming the import. ✅
**Scenario "Port-only cross-app edge"**: negative-gate verified — port import PASSED (whitelist), adapter import FAILED. ✅

### Req: Test Infrastructure — ✅ PASS
| Spec | Implementation | Status |
|---|---|---|
| pytest + pytest-django configured, DJANGO_SETTINGS_MODULE=config.settings | `[tool.pytest.ini_options]` with DJANGO_SETTINGS_MODULE=config.settings, pythonpath=["."], testpaths=["tests"], db marker | ✅ |
| Tests target dedicated Postgres test DB via DATABASE_URL | `tests/conftest.py::_test_database_url()` derives `test_<db>` from DATABASE_URL | ✅ |
| Session fixture runs prisma migrate deploy | `prisma_test_db` session fixture runs `prisma migrate deploy` with test URL | ✅ |
| Smoke test writes/reads via Prisma | `test_db_smoke.py`: create client (Ana Gomez) → find_unique → delete roundtrip | ✅ |
| strict_tdd re-enabled after pytest lands | `config.yaml`: top-level `strict_tdd: true` (L11), `testing.strict_tdd: true` (L14), `rules.apply.tdd: true` + `test_command: "uv run pytest"` (L53–54), `rules.verify.test_command` (L56) | ✅ |

**Scenario "Test DB has Prisma tables"**: `uv run pytest -v` → 2 passed (health + DB smoke with real Postgres roundtrip), exit 0. ✅
**Scenario "Fixture fails fast without Postgres"**: DATABASE_URL pointed at unreachable port 59999 → session fixture errored at setup with psycopg `ConnectionTimeout` (connect_timeout=5), exit 1. Fast failure confirmed. ✅

## 2. Task checklist — 23/23 complete
All tasks marked `[x]` in tasks.md (1.1–1.5, 2.1–2.3, 3.1–3.6, 4.1–4.7, 5.1–5.4, 6.1–6.2, 7.1–7.5, 8.1–8.3). 0 incomplete.

## 3. Gates executed (all green)
| Gate | Command | Result |
|---|---|---|
| Lint | `uv run lint-imports` | 9 KEPT / 0 BROKEN, exit 0 |
| Tests | `uv run pytest -v` | 2 passed (health 200 + Prisma DB roundtrip), exit 0 |
| Django | `uv run python manage.py check` | "System check identified no issues (0 silenced)", exit 0 |
| Migrations | `uv run python manage.py makemigrations --check --dry-run` | "No changes detected", exit 0 |
| Prisma | `uv run prisma validate` | schema valid 🚀, exit 0 |
| Docker | `docker ps` | rapidfood_db Up (healthy), 0.0.0.0:5432->5432 |

## 4. Negative-gate validation (gates provably work)
Temporary files created, contracts intentionally broken, then removed; repo restored to green after each:
- `apps/order/application/use_cases/_verify_tmp_framework.py` (imports prisma) → **"Domain, ports and use cases must not import frameworks" BROKEN** ✅
- `apps/order/adapters/inbound/http/_verify_tmp_adapter.py` (imports client's prisma repository) → **"No inbound HTTP adapter to outbound adapter" BROKEN** + **"order consumes siblings only via application.ports" BROKEN** ✅
- `apps/order/application/use_cases/_verify_tmp_port.py` (imports `apps.client.application.ports.outbound.client_query_port`) → port edge **PASSED** (whitelist matched; unmatched-warning for that entry disappeared) ✅
- After deleting all three: lint-imports restored to 9 KEPT / 0 BROKEN (117 files, 23 deps).

## 5. Strict TDD compliance
- Config: `strict_tdd: true` (top-level + testing) and `rules.apply.tdd: true` with `test_command: "uv run pytest"` — **enabled** ✅
- Tests exist for the behavioral seams of this infra change (health endpoint, Prisma DB roundtrip) and pass.
- TDD Cycle Evidence table: **NOT FOUND** — no `apply-progress.md` exists anywhere in the repo (glob `**/apply-progress*` → no files). Per strict-TDD verify protocol, the apply phase was required to record RED/GREEN/TRIANGULATE cycles in an apply-progress artifact; it did not. Flagged CRITICAL (process), though this change is infrastructure-only with no business logic and all tasks carry verification steps.

## 6. Issues

### CRITICAL
1. **Missing apply-progress.md / TDD Cycle Evidence** — Strict TDD was enabled (`rules.apply.tdd: true`) but the apply phase produced no TDD evidence artifact. All functional gates pass and tests exist/pass, so this is a process-evidence gap, not a functional defect. **Before archive**: apply agent must backfill `openspec/changes/scaffold-inicial/apply-progress.md` with the TDD Cycle Evidence table (or orchestrator formally waives evidence for infra-only changes).

### WARNING
2. **Spec text says "16 entities" / scenario "all 16 entities"** — the spec's own list enumerates 15; design.md documents the correction to 15; implementation matches design. Spec text should be aligned (or the deviation accepted as already documented in design).
3. **OrderDraftPort scenario path drift** — scenario says `application.ports.outbound.OrderDraftPort`; design + implementation place it in `application/ports/inbound/` (it is the inbound contract). Import resolves; intent satisfied.
4. **Migration path drift** — spec says commit `prisma/migrations/`; implementation committed root `migrations/` (Prisma default layout with root schema.prisma). README documents `migrations/<ts>_init/`. Functional intent (initial migration committed) satisfied.
5. **Django version drift** — spec purpose says "Django 5"; `pyproject.toml` constrains `django>=5.0` and uv resolved **6.0.7** (DRF 3.17.1). Constraint satisfies spec; installed version is a superset.

### SUGGESTION
6. `Config_couponConfig` class name in `apps/config_coupon/apps.py` is cosmetically awkward (auto-generated from app label); consider renaming to `ConfigCouponConfig`.
7. Keep the `unmatched_ignore_imports_alerting = "warn"` setting — port whitelist entries are untested until real cross-app edges land in later changes; the negative-gate proof shows they work.
8. Consider adding `.atl/` artifacts (apply-progress, verify-report pointer) so the openspec store and agent-skill workflow stay in sync.

## 7. Final verdict

**PASS WITH WARNINGS** — all 7 ADDED requirements implemented and verified, all 6 gates green, all 23 tasks complete, architecture contracts provably enforced (positive + negative), tests real (no tautologies), DB roundtrip real. The change is functionally ready; archive must not proceed until the CRITICAL process finding (#1) is resolved.

## 8. Orchestrator resolution of CRITICAL #1 (TDD evidence gap)

- **Date**: 2026-08-03
- **Decision**: **Waiver granted + evidence backfilled** (option c, chosen by user).
- **Rationale for waiver**: `scaffold-inicial` is infrastructure-only — no business logic, no behavioral seams beyond the health endpoint and Prisma DB roundtrip. Both seams have passing tests (`tests/test_health_smoke.py`, `tests/test_db_smoke.py`). Re-running RED/GREEN cycles post-hoc would add no functional value; the gates prove the tests are real (negative-gate validation in §4). Waiver does NOT set precedent for business-logic changes — those MUST record live TDD cycles.
- **Action taken**: `openspec/changes/scaffold-inicial/apply-progress.md` backfilled by the apply agent (reconstructing the TDD cycle evidence from the executed work + gate outputs in §3/§4), per user decision.
- **Status**: CRITICAL #1 **RESOLVED**. Change eligible for archive.
