# Exploration: scaffold-inicial

**Change**: `scaffold-inicial` — Django + DRF + Prisma Client Python + PostgreSQL + import-linter monorepo for 5 parallel apps (client, conversation, order, catalog, config_coupon)
**Date**: 2026-08-03
**Explorer**: sdd-explore (openspec mode)

---

## 1. Executive Summary

- Repo has **zero application code** (only `docs/`, `openspec/`, `skills/`, `.atl/`, `.git`). Verified toolchain: Python 3.13.1, uv 0.11.7, Docker 27.3.1 + Compose v2.30.3. **psql is NOT installed** → Postgres must run via Docker.
- **Prisma Client Python REPLACES Django's ORM.** Recommended pattern: zero `django.db.models` anywhere; Django/DRF is used only as the inbound HTTP layer (settings, URL routing, DRF viewsets/serializers); the generated Prisma client lives exclusively inside outbound repository adapters; use cases orchestrate via ports.
- **Migrations:** `prisma migrate dev` is the ONLY source of truth for domain tables. Django's `makemigrations`/`migrate` must produce nothing (empty `models.py`; minimal `INSTALLED_APPS`). `prisma generate` regenerates the client after schema changes.
- **Sync client** (`interface = "sync"`) recommended: Django views are sync by default; the async client inside sync views needs `async_to_sync`/`asyncio.run` and has event-loop binding pitfalls. Switching later is just regenerating the client.
- **import-linter** is static (AST-based): works in CI without Django setup or a DB. Strategy: one `layers` contract per app (adapters → application → domain, via `containers`) + `forbidden` contracts for framework leakage (domain/use-cases vs django/drf/prisma) and for port-only cross-app consumption.
- **5-app split matches the Notion plan and the domain docs**, with one gap: the plan lists only QUERY ports (ClientQueryPort, ProductQueryPort, CouponQueryPort, BusinessConfigQueryPort), but the conversation app also needs **command ports into order** (create draft, add line, apply coupon, confirm) per REQ-015..021/036. This must be added to the proposal's port inventory.
- **Biggest risk:** Django's test runner + Prisma — `pytest-django` creates a test DB but nothing creates the Prisma tables; a session fixture running `prisma migrate deploy` against the test DB is mandatory.

## 2. Current State

- Layout: `.atl/`, `docs/`, `openspec/`, `skills/` + `.git`. No code, no `pyproject.toml`, no schema, no compose file yet.
- `openspec/config.yaml` already records the planned stack and hexagonal 5-app architecture; testing config is "no runner yet, pytest planned" — the scaffold must land pytest + pytest-django.
- Domain sources read: `docs/modelo-dominio.md` (16 entities), `docs/order-state-machine.md` (BORRADOR → PENDIENTE → PAGADO/CONFIRMADO → EN_PREPARACION → LISTO → ENTREGADO/RETIRADO, CANCELADO), `docs/reglas-negocio.md` (RN-001..041), `docs/req-funcionales.md` (REQ-001..053), `skills/hexagonal-architecture/SKILL.md`.
- SDD state: `explore` is the first phase of `scaffold-inicial` (all others pending).

## 3. Stack Integration Analysis

### 3.1 Prisma Client Python + Django — the pattern

Verified against official docs (`prisma-client-py.readthedocs.io` / repo docs, PyPI):

- Package: `prisma` on PyPI, latest **0.15.0**, `requires-python >=3.8` → OK on Python 3.13.1. The pip package ships its own CLI (`prisma` with `py generate`, `migrate dev|deploy`, `db push`, `generate`, `studio`); Prisma engine binaries are downloaded at install time (needs network; relevant for CI/teammates).
- **Schema-first**: `schema.prisma` is the single model source. `prisma py generate` (or `prisma generate`) generates a typed client; default output goes INTO the installed `prisma` package → usage is `from prisma import Prisma`.
- **Client lifecycle**: `db = Prisma(); db.connect()` (sync) or `await db.connect()` (asyncio); model access via `db.order.find_many(...)`, nested writes, `include`, `group_by`. Context manager: `async with Prisma() as db:`. `Prisma(auto_register=True)` / `prisma.register(...)` enables model-based access.
- **Two interfaces** selected in the schema generator:
  ```prisma
  generator client {
    provider             = "prisma-client-py"
    interface            = "sync"   // or "asyncio"
    recursive_type_depth = 5
  }
  ```
- **Migrations**: `prisma migrate dev --name "..."` creates + applies a SQL migration AND regenerates the client; `prisma migrate deploy` applies committed migrations non-interactively (CI, test DBs); `prisma db push` syncs schema without migration history (throwaway dev only).

**Recommended pattern for this repo:**

- **No Django models at all.** Each Django app is a normal Python package with `domain/`, `application/ports/{inbound,outbound}/`, `application/use_cases/`, `adapters/inbound/http/`, `adapters/outbound/prisma/`, `composition/` (exactly the hexagonal skill layout). `models.py` stays empty/absent so `makemigrations` is a no-op.
- Django provides: `config/` settings package, URL routing, DRF viewsets + serializers (inbound adapters), WSGI/ASGI entry, and the `manage.py` entry point. DRF serializers map HTTP ↔ use-case DTOs (mapping stays in adapters).
- The generated Prisma client is **confined to outbound adapters** (e.g. `apps/order/adapters/outbound/prisma/prisma_order_repository.py`). Domain and use cases never import `prisma`, `django`, or `rest_framework` — this is what satisfies the hexagonal rule "domain must NOT import framework/ORM types" and keeps use cases testable with in-memory fakes.
- **Composition root**: one `composition/container.py` per app builds repositories (receiving the Prisma client instance via constructor) and injects them into use cases; DRF views receive use cases via the container. A single shared Prisma instance (lazy singleton, e.g. `config/db.py`) is `connect()`ed once at process start and `disconnect()`ed on shutdown — never per request.

### 3.2 Migrations — source of truth

- **Prisma schema + `prisma/migrations/` = the ONLY source of truth** for all domain tables.
- Django migration machinery is effectively disabled: apps have no models, so `makemigrations` produces nothing. If Django contrib apps are enabled, their tables would come from Django's `migrate` — **decision: keep `INSTALLED_APPS` minimal** (at most `django.contrib.staticfiles`) so two migration systems never fight over one DB. Note: REQ-001..053 contain **no authentication requirements** — no `auth`/`sessions`/`admin` needed in the scaffold (Prisma Studio covers data browsing).
- Workflow per developer: edit `schema.prisma` → `uv run prisma migrate dev --name "..."` → commit schema + migration. Teammates: `uv run prisma migrate deploy`. Tests/CI: `prisma migrate deploy` against the (test) database.

### 3.3 Sync vs Async client — decision

| | Sync (`interface = "sync"`) | Async (`interface = "asyncio"`) |
|---|---|---|
| Django WSGI sync views | Direct `db.order.create(...)`, no await | Needs `asyncio.run`/`async_to_sync` per call — error-prone |
| Event loop binding | None | Engine binds to creating loop; cross-loop use breaks |
| Tests (pytest, sync) | Simple | Requires async test plugin (pytest-asyncio) + pytest-django async support |
| Future ASGI/async views | Blocks loop — would need to switch | Ready |

**Recommendation: `sync`.** Django's default request path is sync WSGI; the scaffold has no async requirements (REQ-001..053 are HTTP CRUD + agent orchestration). Switching later is a one-line schema change + `prisma generate` + adapter call-site edit (drop `await`), which the port boundaries contain nicely.

## 4. import-linter Contract Strategy

Facts (verified against import-linter docs):

- Config in `pyproject.toml`: `[tool.importlinter]` + one or more `[[tool.importlinter.contracts]]`.
- Requires `root_package` (single) or `root_packages` (multiple). Contracts available: `layers`, `forbidden`, `protected`, `independence`, `acyclic`.
- `layers` supports `containers` (parent modules of the layer list) → one layered contract can be applied under each of the 5 apps.
- `forbidden` supports wildcards (`*`, `**`), `as_packages = false` (descendant rules), `include_external_packages = true` (forbid django/rest_framework/prisma), and `ignore_imports` for exceptions.
- Runner: `lint-imports` (optionally `--contract <name>`). Static analysis → no Django setup, no DB → fast CI gate.

**Proposed contracts (finalize exact syntax in design phase):**

1. **Hexagonal layers inside each app** (one contract, `containers` = the 5 apps):
   ```toml
   [tool.importlinter]
   root_package = "apps"

   [[tool.importlinter.contracts]]
   name = "Hexagonal layers inside each app"
   type = "layers"
   containers = ["apps.client", "apps.conversation", "apps.order", "apps.catalog", "apps.config_coupon"]
   layers = [
     "adapters.inbound.http",      # DRF views/serializers (highest)
     "adapters.outbound",          # prisma repositories / gateways
     "application.ports.inbound",  # inbound port interfaces
     "application.use_cases",      # orchestration
     "application.ports.outbound", # outbound port interfaces
     "domain",                     # pure domain (lowest)
   ]
   ```
   ⚠️ A `layers` contract forbids importing HIGHER layers, but it **cannot** express "no adapter → adapter" (same-direction extras like `adapters.inbound.http → adapters.outbound` are allowed because the target is lower). So the layers contract MUST be paired with the forbidden contracts below.

2. **Domain/use-case purity (framework ban)**:
   ```toml
   [tool.importlinter]
   root_package = "apps"
   include_external_packages = true

   [[tool.importlinter.contracts]]
   name = "Domain must not import frameworks"
   type = "forbidden"
   source_modules = ["apps.*.domain", "apps.*.application.use_cases"]
   forbidden_modules = ["django", "rest_framework", "prisma"]
   as_packages = false
   ```
   (`django.db.models`, DRF, and the generated Prisma client all become unreachable from domain/use-cases.)

3. **Cross-app consumption only via ports**:
   ```toml
   [[tool.importlinter.contracts]]
   name = "Apps consume each other only via application.ports"
   type = "forbidden"
   source_modules = ["apps.client", "apps.conversation", "apps.order", "apps.catalog", "apps.config_coupon"]
   forbidden_modules = ["apps.*"]   # any sibling app
   ignore_imports = [
     "apps.conversation -> apps.order.application.ports",
     "apps.conversation -> apps.catalog.application.ports",
     "apps.conversation -> apps.client.application.ports",
     "apps.conversation -> apps.config_coupon.application.ports",
     "apps.order -> apps.client.application.ports",
     "apps.order -> apps.catalog.application.ports",
     "apps.order -> apps.config_coupon.application.ports",
     # ... remaining port edges
   ]
   ```
   Design phase must validate wildcard semantics in `ignore_imports`; an alternative shape is explicit per-pair forbidden contracts (more verbose but easier for 5 students to read). Optionally add an `acyclic` contract over the 5 apps to forbid circular app imports.

Operational note: import-linter resolves dotted module names, so `apps/` must be a real Python package (`apps/__init__.py` present) — also convenient for Django `INSTALLED_APPS = ["apps.order", ...]`.

## 5. Prisma Schema — Open Decisions (tradeoffs, NOT the schema)

Derived from `docs/modelo-dominio.md` (16 entities: businessConfiguration, businessHours, address, client, conversation, message, order, orderLine, product, price, category, discount, coupon, appliedCoupon, payment). These decisions belong in the proposal/design — listed here with tradeoffs:

### D1. IDs: UUID vs Int autoincrement
- Domain uses semantic IDs (orderId, clientId, conversationId, productId, couponId...).
- **A) `String @id @default(uuid())`** — unguessable, safe to share across app boundaries (conversation → order), uniform, no enumeration. Cons: larger index, unreadable in logs, no ordering.
- **B) `Int @id @default(autoincrement())`** — compact, fast, readable. Cons: enumerable, leaks cross-app traffic counts.
- **C) `String @id @default(cuid())`** — like UUID, more compact.
- **Lean A (UUID)**, stored native `@db.Uuid` in Postgres. Cross-app references (agent conversation references orders by id) favor non-sequential public IDs. Decision to confirm in design.

### D2. Enums
Prisma `enum` → native Postgres enum. Candidates with fixed vocabulary from the docs:
- `OrderStatus`: BORRADOR, PENDIENTE, PAGADO, CONFIRMADO, EN_PREPARACION, LISTO, ENTREGADO, RETIRADO, CANCELADO (state machine + RN-001..019)
- `DeliveryType`: ENVIO, RETIRO
- `PaymentType`: EFECTIVO, ONLINE (docs only distinguish these two; extend later if providers arrive)
- `PaymentStatus`: PENDIENTE, APROBADO, RECHAZADO, FALLIDO, VENCIDO (RN-038..040, REQ-049)
- `WeekDay` (businessHours.openWeekDay): LUNES..DOMINGO vs `Int` 0-6 — pick enum for readability
- Open vocab → **String, not enum**: `conversation.channel`, `message.detectedIntent`, `message.sentiment`, `message.status`, `message.role` (docs give no value lists; design must define them, or leave String with app-level validation).

Tradeoff: native enums are type-safe/validated/readable but altering values requires `ALTER TYPE` migrations (annoying). Use enums ONLY where the docs fix the vocabulary; String elsewhere.

### D3. Money: Decimal vs Float vs Int cents
Money fields: `price.price`, `coupon.amount`, `appliedCoupon.amount`/`discountAmount`, `order.shippingCost`/`totalAmount`, `orderLine.subtotal` (+ `orderLine.amount` is likely quantity — confirm).
- **A) `Decimal @db.Decimal(10, 2)`** → Python `Decimal`. Exact, correct for money, readable, DB-native. Slightly slower. **Lean A.**
- **B) `Float`** — binary rounding, WRONG for money.
- **C) Int cents** — exact integer math but conversion overhead, less readable, error-prone for students.
- `discount.percentage`: `Decimal(5,2)` (0–100) or Int basis points — pick in design.

### D4. Relations & snapshot rules (from the class diagram)
- `businessConfiguration` 1—* `businessHours`; `businessConfiguration` 1—* `address`; `address` 1—* `order` (`order.addressId` FK). **Ambiguity**: businessConfiguration ALSO has a literal `adress` attribute (typo) plus a 1..* relation to the Address class. Decision needed: Address = own table owned by businessConfiguration; `order.addressId` **nullable** until confirm (RN-020: BORRADOR needs no full address).
- `client` 1—* `conversation`; `client` 1—* `order`; `conversation` 1—* `message`; `order` 1—* `orderLine`; `product` 1—* `orderLine`; `product` 1—* `price` (price history keyed by `sinceDate`); `category` 1—* `product`; `order` 1—* `appliedCoupon`; `coupon` 1—* `appliedCoupon`; `order` 1—* `payment`; `orderLine` 0..1 `discount` (FK nullable).
- **Price freezing (RN-024/035, REQ-023)**: `orderLine` must store a `unitPrice` SNAPSHOT column (not a relation to price history) — RN-026/27 make line prices immutable after confirm.
- **Coupon snapshot (RN-033/034)**: `appliedCoupon` duplicates coupon fields (couponCode, type, amount, availableUses, dateOfExpiration) + `appliedAt` — correct snapshot pattern, keep.
- **Conversation ↔ draft (RN-028/030, REQ-038)**: `order.conversationId` FK nullable (set while drafting). "One active BORRADOR per conversation" cannot be a plain `@@unique` (partial unique index not supported by Prisma) → enforce in the use case (or a trigger); flag for design.
- **Naming**: Prisma defaults to camelCase fields + model-named tables → recommend `@map("snake_case")` on every field and `@@map("snake_case")` on every model so SQL is standard. Mechanical, cheap now, painful later — good scaffold task.
- **Timestamps**: `createdAt @default(now())` everywhere; `updatedAt @updatedAt` where the docs list it (payment).

### D5. Schema location & generated client output
- Single root `schema.prisma` shared by all 5 apps (one DB, one service) — matches the plan.
- Generator output: default (inside venv `prisma` package) vs explicit `output = "../generated"`. Default = nothing to commit; explicit dir = IDE-visible types but must be gitignored and regenerated. Lean default + `uv run prisma generate` as a documented setup step (scaffold adds a script/Makefile target). Confirm in design.

## 6. Recommended Monorepo Layout

```
rapidfood/
├── pyproject.toml          # uv project; deps: django, djangorestframework, prisma, psycopg[binary],
│                           # import-linter, pytest, pytest-django; [tool.importlinter] contracts
├── uv.lock
├── manage.py
├── schema.prisma           # single source of truth (all 16 entities)
├── prisma/
│   └── migrations/         # prisma migrate dev output (committed)
├── config/                 # Django project package
│   ├── __init__.py
│   ├── settings.py         # INSTALLED_APPS = the 5 apps (+ staticfiles); DATABASES via env
│   ├── urls.py             # routes → each app's inbound adapters
│   ├── wsgi.py / asgi.py
│   └── db.py               # Prisma client lazy singleton (shared infra, composition root)
├── apps/
│   ├── __init__.py         # real package → import-linter dotted paths + INSTALLED_APPS
│   ├── client/             # domain/ application/{ports/{inbound,outbound},use_cases}/
│   │                       # adapters/{inbound/http,outbound/prisma}/ composition/
│   ├── conversation/       # (same shape)
│   ├── order/              # (same shape)
│   ├── catalog/            # (same shape)
│   └── config_coupon/      # (same shape)
├── docker-compose.yml      # postgres:16, named volume, healthcheck, port 5432, .env-driven
├── .env.example            # DATABASE_URL=postgresql://rapidfood:rapidfood@localhost:5432/rapidfood
├── .gitignore              # .env, .venv, __pycache__, generated prisma artifacts
└── tests/                  # pytest + pytest-django; conftest with prisma migrate deploy fixture
```

## 7. 5-App Split vs Notion Plan

- The 4 query ports (ClientQueryPort, ProductQueryPort, CouponQueryPort, BusinessConfigQueryPort) cover READ paths for the agent (conversation) and order flows. Consistent with the domain docs.
- **GAP — command ports missing from the plan**: conversation must trigger draft lifecycle: create draft (REQ-015), add/update/remove lines (REQ-016..018), apply/remove coupon (REQ-020), confirm → PENDIENTE (REQ-021/036), abandon (REQ-024), query draft (REQ-038), and handle the "one draft per conversation" rule (RN-028/029). The proposal must add an inbound-facing port from the order app — e.g. `OrderDraftPort` (create, addLine, removeLine, setQuantity, applyCoupon, confirm, abandon) — and a `ClientCommandPort` (agent registers clients).
- Payment lives in the **order** app (payment entity, RN-038..041) with an outbound `PaymentGatewayPort` (mocked in scaffold).
- The agent itself (conversation app) is the orchestrator per REQ-027..037/040..041/052..053; actual NLP/LLM is out of scaffold scope (infra + skeleton only).
- **Verdict**: split matches the plan. Open ownership questions to confirm: address (businessConfiguration vs order), client creation (client app owns Client; order/conversation consume ports), and the command-port inventory.

## 8. Risks and Open Questions

### Risks
1. **Django test runner vs Prisma migrations (HIGH)**: pytest-django creates `test_<db>` but nothing creates Prisma tables → every DB test fails unless a session fixture runs `prisma migrate deploy` against the test DB (and Django's own migration-based setup is bypassed). Mitigation: include `tests/conftest.py` fixture in the scaffold; design phase specifies exact flow.
2. **Two migration systems**: enabling contrib apps (auth/admin/sessions) makes Django `migrate` create its own tables and confuses ownership. Mitigation: minimal `INSTALLED_APPS` (staticfiles only) in scaffold; document "Prisma owns ALL tables".
3. **Engine binaries at install**: `uv sync` downloads Prisma engines (network); teammates/CI must run `uv sync` + `uv run prisma generate`. Mitigation: documented setup script / Makefile target in scaffold tasks.
4. **import-linter semantics**: `layers` cannot forbid adapter→adapter; wildcard behavior in `ignore_imports` needs validation. Mitigation: layers + complementary forbidden contracts; validate with a small spike during scaffold.
5. **Enum evolution**: native Postgres enums are painful to alter. Mitigation: enums only for doc-fixed vocabularies; String for open vocab (intent, channel, role).
6. **Sync client limits**: if the team later wants ASGI/async views, sync client blocks the loop. Accepted for scaffold; documented switch path.
7. **Schema naming**: default camelCase leaks into SQL; decide `@map`/`@@map` convention NOW (scaffold).

### Open Questions (for proposal/design)
- Q1: Which Django contrib apps in `INSTALLED_APPS`? (Recommend: `staticfiles` only — no auth/sessions/admin.)
- Q2: Confirm **sync** client for scaffold?
- Q3: Address ownership: businessConfiguration owns Address; `order.addressId` nullable until confirm; coverage check via BusinessConfigQueryPort — confirm.
- Q4: Who creates Client records? (client app use case; conversation consumes ClientQueryPort + ClientCommandPort.)
- Q5: Command-side port inventory (OrderDraftPort, ClientCommandPort) — must be written into the proposal.
- Q6: Generated client output: default (venv) vs explicit dir?
- Q7: Postgres version pin (16.x LTS recommended) and whether to add a Prisma Studio service or run `uv run prisma studio`.
- Q8: pytest + pytest-django (recommended, config.yaml already plans pytest) vs Django TestCase.
- Q9: `orderLine.amount` semantics (quantity?) and `discount.percentage` precision — confirm with domain docs.

---

## Ready for Proposal
**Yes.** The orchestrator should tell the user: the Prisma+Django pattern is sound and well-documented (Prisma replaces Django models; migrations via `prisma migrate dev` only; sync client), import-linter gives a concrete 3-contract strategy, and the scaffold must include a Prisma-aware test fixture. The proposal should add the missing command ports (OrderDraftPort, ClientCommandPort) and resolve Q1-Q9 above.
