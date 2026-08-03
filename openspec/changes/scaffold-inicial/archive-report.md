# Archive Report — scaffold-inicial

- **Change**: scaffold-inicial
- **Project**: rapidfood
- **Mode**: openspec (filesystem artifacts)
- **Archived**: 2026-08-03
- **Executor**: sdd-archive executor
- **Verdict at archive**: PASS WITH WARNINGS — CRITICAL #1 resolved (waiver + backfilled apply-progress)
- **Blocking for archive**: none

## Change Summary

`scaffold-inicial` laid the shared foundation for the rapidfood monorepo: a uv-managed Python 3.13 project where Django 6.0.7 + DRF acts only as the inbound HTTP layer and **Prisma Client Python owns all persistence** (zero Django models). It delivered five empty hexagonal apps (client, conversation, order, catalog, config_coupon) with port contracts, the Prisma data model (15 entities, 5 enums), Postgres 16 via Docker, import-linter architecture enforcement (9 contracts), and pytest infrastructure whose session fixture runs `prisma migrate deploy` against the test DB. This unblocks the 5-person team to run Strict TDD in parallel on per-app business logic.

## Delivered

- **Project setup**: `pyproject.toml` + `uv.lock` (Python 3.13; django, djangorestframework, prisma, psycopg[binary], import-linter, pytest, pytest-django), `docker-compose.yml` (Postgres 16, named volume, healthcheck), `.env.example`, `.gitignore`, README with setup steps (documents network as a prerequisite).
- **Django shell**: `manage.py` + `config/` (settings, urls, wsgi/asgi, `db.py` Prisma lazy singleton); `GET /health` → 200 `{"status": "ok"}`; INSTALLED_APPS = staticfiles + rest_framework + 5 apps only (no auth/sessions/admin); sqlite in-memory DATABASES placeholder so pytest-django machinery runs without touching Postgres; Prisma alone reads DATABASE_URL.
- **Hexagonal app structure**: `apps/` real package with 5 apps, each carrying `domain/`, `application/ports/{inbound,outbound}/`, `application/use_cases/`, `adapters/{inbound/http,outbound/prisma}/`, `composition/` (all packages); empty `models.py`.
- **Port inventory**: 6 contract-only Protocol modules with frozen DTOs — ClientQueryPort, ClientCommandPort, ProductQueryPort, CouponQueryPort, BusinessConfigQueryPort, OrderDraftPort (inbound, in `apps/order/application/ports/inbound/`); zero framework imports.
- **Prisma data model**: single root `schema.prisma` (postgresql datasource, `interface = "sync"`), 15 models, 5 enums (OrderStatus with 9 states per RN-001), UUID ids, Decimal(10,2) money, snapshots (`orderLine.unitPrice` RN-024/035, `appliedCoupon` full coupon copy RN-033/034), nullable `order.addressId`/`conversationId`, snake_case via @map/@@map; initial migration committed at `migrations/20260803222839_init/`.
- **Architecture contracts**: import-linter — per-app layers, http→outbound forbidden, framework ban (django/rest_framework/prisma) on domain+use_cases, per-app sibling forbidden with `ignore_imports` whitelisting `application.ports`, acyclic. `uv run lint-imports`: 9 KEPT / 0 BROKEN.
- **Test infrastructure**: pytest + pytest-django (`DJANGO_SETTINGS_MODULE=config.settings`), `tests/conftest.py` session fixture (`prisma_test_db` runs `prisma migrate deploy` against `test_<db>`; `db` session Prisma client), `tests/test_health_smoke.py`, `tests/test_db_smoke.py` (real write/read/delete roundtrip); fail-fast without Postgres.
- **Config**: `strict_tdd: true` re-enabled (top-level + `testing.strict_tdd` + `rules.apply.tdd` with `test_command: "uv run pytest"`).

## Verification Verdict

**PASS WITH WARNINGS** — all 7 ADDED requirements met, all 6 gates green (lint-imports 9 KEPT / 0 BROKEN; pytest 2 passed incl. real Postgres roundtrip; `manage.py check` clean; `makemigrations` no-op; `prisma validate` valid; Docker healthy), all 23 tasks complete, architecture contracts provably enforced via positive + negative-gate validation (§4 of verify-report).

CRITICAL #1 (missing TDD Cycle Evidence / apply-progress.md) was resolved 2026-08-03 per the orchestrator resolution recorded in verify-report §8: **waiver granted** (infrastructure-only change — no business logic, only two behavioral seams, both with passing tests; waiver does NOT set precedent for business-logic changes) **+ apply-progress.md backfilled** by the apply agent with the reconstructed TDD cycle evidence. Change eligible for archive.

## Known Deviations (verify-report §6)

1. **16 vs 15 entities**: spec text and scenario say "16 entities" but the spec's own list enumerates 15; design.md documents the correction to 15 and the implementation (and `prisma validate`/migration) matches the design. Accepted as documented in design.
2. **OrderDraftPort path drift**: spec scenario says `application.ports.outbound.OrderDraftPort`; design + implementation place it in `application/ports/inbound/` (it is the inbound contract the conversation agent calls). Import resolves; intent satisfied.
3. **Migration path drift**: spec says commit `prisma/migrations/`; implementation committed root `migrations/` (Prisma default layout with a root `schema.prisma`). README documents `migrations/<ts>_init/`. Functional intent (initial migration committed) satisfied.
4. **Django wording**: spec purpose says "Django 5"; `pyproject.toml` constrains `django>=5.0` and uv resolved **Django 6.0.7** / DRF 3.17.1 — a superset satisfying the constraint.
5. **Suggestions** (§6 #6–8) left for future changes: `Config_couponConfig` cosmetic rename, keep `unmatched_ignore_imports_alerting = "warn"`, add `.atl/` sync pointers. None block archive.

## Synced to Main Specs

- `openspec/specs/` was empty (greenfield, only `.gitkeep`) → the delta spec is the full spec.
- **Created** `openspec/specs/scaffold/spec.md` from `openspec/changes/scaffold-inicial/specs/scaffold/spec.md`: 7 ADDED requirements promoted to plain `## Requirements` (delta framing removed), all 7 requirements, 11 scenarios, and RFC 2119 language preserved verbatim. No requirements lost, no merge conflicts possible (no prior main spec).

## Archive Actions

- `openspec/specs/scaffold/spec.md` — created (source of truth updated).
- `openspec/changes/scaffold-inicial/state.yaml` — `phases.archive: in_progress` → `done`.
- Folder retained in place at `openspec/changes/scaffold-inicial/` per orchestrator instruction (state marker `archive: done` records closure; full audit trail — proposal, design, delta spec, tasks, apply-progress, verify-report, archive-report — intact). Not moved to `openspec/changes/archive/`.
- `openspec/config.yaml` — **unchanged**: the `testing.note` ("pytest + pytest-django installed by scaffold-inicial") still reads correctly — pytest infrastructure persists in the codebase after the change closes — and `strict_tdd: true` is correctly active. Nothing stale.

## Next Recommended

**`order-draft`** — the first business-logic change: implement the draft-order flow behind the already-shipped `OrderDraftPort` (inbound) — use cases in `apps/order/application/use_cases/`, Prisma adapter in `apps/order/adapters/outbound/prisma/`, wired via `composition/container.py`, developed Strict-TDD style on top of the existing test-DB fixture. This exercises the full hexagonal stack (ports → use cases → adapter → Postgres) and RN-004/RN-020/RN-023/RN-024/RN-028/RN-030/RN-031/RN-032 rules. Deferred alternative: the CI pipeline (explicitly out of scope in the proposal).
