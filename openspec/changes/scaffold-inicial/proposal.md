# Proposal: scaffold-inicial

## Intent

Lay the shared foundation for the rapidfood monorepo: a uv-managed Django 5 + DRF project where **Prisma Client Python replaces Django's ORM** (Django is only the inbound HTTP layer), five empty hexagonal Django apps (client, conversation, order, catalog, config_coupon) with full folder skeletons and port contracts, the Prisma schema covering all 16 entities from `docs/modelo-dominio.md`, Docker Postgres, import-linter architecture enforcement, and pytest infrastructure. This unblocks the 5-person team to run Strict TDD in parallel on per-app business logic without redoing infrastructure.

## Scope

### In Scope
- uv project init (`pyproject.toml` + `uv.lock`); deps: django, djangorestframework, prisma, psycopg[binary], import-linter, pytest, pytest-django
- Django 5 + DRF skeleton: `config/` settings package, `manage.py`, URL routing, `/health` endpoint
- 5 empty apps with hexagonal skeleton: `domain/`, `application/ports/{inbound,outbound}/`, `application/use_cases/`, `adapters/{inbound,outbound}/`, `composition/`
- Port interfaces (contracts only, no impl): ClientQueryPort, ProductQueryPort, CouponQueryPort, BusinessConfigQueryPort + **OrderDraftPort** (create/addLine/removeLine/setQuantity/applyCoupon/confirm/abandon) + **ClientCommandPort**
- `schema.prisma` with ALL 16 entities (businessConfiguration, businessHours, address, client, conversation, message, order, orderLine, product, price, category, discount, coupon, appliedCoupon, payment) + initial `prisma/migrations/`
- `docker-compose.yml` (Postgres 16), `.env.example`, `.gitignore`
- import-linter contracts: (1) hexagonal layers per app, (2) framework ban on domain/use-cases, (3) cross-app consumption only via ports
- pytest + pytest-django + `tests/conftest.py` fixture running `prisma migrate deploy` on the test DB
- README with setup steps

### Out of Scope
- Business logic / use-case implementations (later per-app changes)
- Endpoints beyond `/health`
- Auth, admin, sessions (no auth requirements in REQ-001..053)
- Django models — `models.py` MUST stay empty; Prisma owns ALL tables
- Seed data beyond a minimal dev fixture
- CI pipeline (later change)

## Capabilities

### New Capabilities
- `project-setup`: uv/Django/DRF skeleton, docker-compose, env, README
- `data-model`: Prisma schema (16 entities), enums, migrations, naming conventions
- `app-structure`: 5 hexagonal apps, folder skeleton, port inventory
- `architecture-contracts`: import-linter layers/framework-ban/cross-app contracts
- `test-infrastructure`: pytest + pytest-django + Prisma test-DB fixture

### Modified Capabilities
None — `openspec/specs/` is empty (greenfield).

## Approach

- **Prisma replaces Django ORM**: zero `django.db.models`; `prisma migrate dev` is the ONLY source of truth for domain tables; `makemigrations` is a no-op. Django/DRF only routes and maps HTTP (inbound adapters).
- **Generated Prisma client confined** to `adapters/outbound/prisma/`; use cases orchestrate via ports; shared lazy singleton in `config/db.py`; per-app `composition/container.py` wires adapters → use cases.
- **Sync client** (`interface = "sync"`): Django views are sync WSGI; no event-loop pitfalls; switching later = schema one-liner + regenerate + drop awaits.
- **import-linter** (static, AST-based, no DB): one `layers` contract with `containers` = the 5 apps, plus `forbidden` contracts (frameworks; sibling apps) with `ignore_imports` for legitimate port edges; `apps/` MUST be a real Python package.
- **Schema decisions**: UUID ids, enums only for fixed vocabulary, `Decimal(10,2)` money, snapshot columns (`orderLine.unitPrice` per RN-024/035; full coupon copy in `appliedCoupon` per RN-033/034), nullable `order.addressId`/`order.conversationId`, snake_case via `@map`/`@@map`. "One active BORRADOR per conversation" (RN-028) is a use-case rule, not a DB constraint.

## Key Decisions

| Decision | Choice | Rationale |
|---|---|---|
| ORM | Prisma, no Django models | single schema source; typed client; Django = HTTP only |
| IDs | `String @id @default(uuid())` (`@db.Uuid`) | non-enumerable, safe across app boundaries |
| Enums | Only fixed vocab: OrderStatus, DeliveryType, PaymentType, PaymentStatus, WeekDay | type-safe; open vocab (channel, intent, role) stays String |
| Money | `Decimal(10,2)`; `discount.percentage Decimal(5,2)` | exact money math |
| Snapshots | `orderLine.unitPrice`, `appliedCoupon` coupon copy | price/coupon freezing (RN-024/026/027/033/034) |
| Schema | single root `schema.prisma`, snake_case maps | one DB/one service; standard SQL naming |
| Client | sync interface | matches sync WSGI views |
| INSTALLED_APPS | staticfiles only | two migration systems never fight; no auth needed |
| Tests | pytest-django + session fixture `prisma migrate deploy` | Prisma tables exist before any DB test |

## Affected Areas

| Area | Impact | Description |
|---|---|---|
| `pyproject.toml`, `uv.lock` | New | deps + `[tool.importlinter]` contracts |
| `manage.py`, `config/` | New | settings, urls, wsgi/asgi, `db.py` |
| `schema.prisma`, `prisma/migrations/` | New | domain model + initial migration |
| `apps/{client,conversation,order,catalog,config_coupon}/` | New | hexagonal skeletons + ports |
| `docker-compose.yml`, `.env.example`, `.gitignore` | New | local infra |
| `tests/` | New | conftest + Prisma fixture |
| `README.md` | New | setup steps |

## Risks

| Risk | Likelihood | Mitigation |
|---|---|---|
| Django test runner creates `test_<db>` but no Prisma tables → every DB test fails | High | session fixture in `tests/conftest.py` runs `prisma migrate deploy` against the test DB |
| Prisma engine binaries download at install (network) | Med | README/Makefile: `uv sync` + `uv run prisma generate` as setup step |
| import-linter `layers` can't forbid adapter→adapter; `ignore_imports` wildcards unverified | Med | complementary `forbidden` contracts; validate with a spike during apply |
| Postgres enums painful to alter | Low | enums only for doc-fixed vocabularies; String elsewhere |

## Rollback Plan

`git revert` the scaffold commit(s). Nothing destructive: no production data exists. If migrations were applied locally, `uv run prisma migrate reset` on the dev DB restores a clean state.

## Dependencies

- Docker (Postgres 16 image)
- Network access for `uv sync` (Prisma engine binaries)
- Python 3.13 + uv 0.11+

## Success Criteria

- [ ] On a clean clone: `uv sync && uv run prisma generate && uv run prisma migrate dev` succeed
- [ ] `uv run django check` passes and `/health` responds 200
- [ ] `uv run pytest` collects and passes, including a DB smoke test via the Prisma fixture
- [ ] `uv run lint-imports` passes all 3 contracts
- [ ] All 5 apps are importable from `INSTALLED_APPS`; `makemigrations` produces no changes
