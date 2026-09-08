# Apply Progress: Mercado Pago Payments

## Status

Second implementation batch complete with Strict TDD evidence merged. Phases 1-2 are green; Phase 3 Prisma persistence code/schema are implemented, but DB-backed GREEN execution is blocked because Postgres at `localhost:5432` timed out in the shared Prisma test fixture.

## Completed Tasks

- [x] 1.1 RED: domain payment tests for lifecycle values, final statuses, and idempotency helper behavior.
- [x] 1.2 GREEN: pure domain `PaymentStatus` and `Payment` models exported from `domain/models/__init__.py`.
- [x] 1.3 RED: create-payment-link use-case tests for missing, not-`PENDING`, non-`ONLINE`, and non-positive-total orders.
- [x] 2.1 GREEN: payment driver DTOs and driven payment repository/provider ports.
- [x] 2.2 RED: payable-order use-case test for pending payment creation, provider call, persisted provider ids/link, and plain response.
- [x] 2.3 GREEN: `CreatePaymentLinkUseCase` with constructor-injected ports only.
- [x] 3.1 RED: Prisma payment repository integration tests for create, lookup by external/preference/reference, status update, and duplicate-safe save.
- [x] 3.2 GREEN: Prisma schema payment trace fields/indexes, migration SQL, and regenerated Prisma client.
- [x] 3.3 GREEN: `PrismaPaymentRepository` plus `payment_mapper.py` implementing the application `PaymentRepository` port.

## TDD Cycle Evidence

| Task | Test File | Layer | Safety Net | RED | GREEN | TRIANGULATE | REFACTOR |
|------|-----------|-------|------------|-----|-------|-------------|----------|
| 1.1 | `api/modules/order/tests/domain/test_payment_domain.py` | Unit | N/A (new) | `uv run pytest api/modules/order/tests/domain/test_payment_domain.py` failed: missing `modules.order.domain.models.payment` | `uv run pytest api/modules/order/tests/domain/test_payment_domain.py` passed: 4/4 | 4 cases: enum values, final statuses, same final duplicate, pending non-duplicate | None needed |
| 1.2 | `api/modules/order/tests/domain/test_payment_domain.py` | Unit | N/A (new files; `domain/models/__init__.py` was empty) | Covered by 1.1 failing imports | `uv run pytest api/modules/order/tests/domain/test_payment_domain.py` passed: 4/4 | Structural domain implementation exercised by 4 domain cases | None needed |
| 1.3 | `api/modules/order/tests/use_cases/test_create_payment_link_use_case.py` | Unit | N/A (new) | `uv run pytest api/modules/order/tests/use_cases/test_create_payment_link_use_case.py` failed: missing `payment_ports`, then missing use case | `uv run pytest api/modules/order/tests/use_cases/test_create_payment_link_use_case.py` passed: 7/7 | 6 invalid scenarios: missing order, not pending, cash, None/zero/negative total | None needed |
| 2.1 | `api/modules/order/tests/use_cases/test_create_payment_link_use_case.py` | Unit | N/A (new ports) | Covered by 1.3 missing `payment_ports` import | `uv run pytest api/modules/order/tests/use_cases/test_create_payment_link_use_case.py` passed: 7/7 after use-case GREEN | Ports exercised through use-case fakes and provider result DTO | None needed |
| 2.2 | `api/modules/order/tests/use_cases/test_create_payment_link_use_case.py` | Unit | N/A (new behavior) | `uv run pytest api/modules/order/tests/use_cases/test_create_payment_link_use_case.py` failed: missing use case | `uv run pytest api/modules/order/tests/use_cases/test_create_payment_link_use_case.py` passed: 7/7 | Happy path plus invalid cases forced real branching and provider persistence | None needed |
| 2.3 | `api/modules/order/tests/use_cases/test_create_payment_link_use_case.py` | Unit | N/A (new use case) | Covered by 2.2 missing use case | `uv run pytest api/modules/order/tests/use_cases/test_create_payment_link_use_case.py` passed: 7/7 | 7 use-case cases total | None needed |
| 3.1 | `api/modules/order/tests/integration/test_prisma_payment_repository.py` | Integration | N/A (new) | `uv run pytest api/modules/order/tests/integration/test_prisma_payment_repository.py` failed: missing `modules.order.infrastructure.adapters.driven.prisma.payment_repository` | DB GREEN blocked: same test collects 4 items, then shared fixture times out connecting to Postgres `localhost:5432` | 4 cases: create/reference lookup, provider data external/preference lookups, status update, duplicate-safe save | None needed |
| 3.2 | `api/modules/order/tests/integration/test_prisma_payment_repository.py` | Integration/schema | Schema validation before DB GREEN | Covered by 3.1 plus missing Prisma fields in planned tests | `uv run prisma generate --schema api/shared/infrastructure/prisma/schema.prisma` passed; `uv run prisma validate --schema api/shared/infrastructure/prisma/schema.prisma` passed | Trace fields include `preferenceId`, `checkoutUrl`, `externalReference`, `providerPayload`, `expiresAt`; `externalId`/`preferenceId` unique and `externalReference` indexed | None needed |
| 3.3 | `api/modules/order/tests/integration/test_prisma_payment_repository.py` | Integration/adapter | N/A (new adapter) | Covered by 3.1 missing repository import | `$env:PYTHONPATH='api'; uv run python -c "from modules.order.infrastructure.adapters.driven.prisma.payment_repository import PrismaPaymentRepository; print(PrismaPaymentRepository.__name__)"` passed; DB GREEN blocked by Postgres timeout | Repository methods exercised by 4 integration cases once DB is available | None needed |

## Verification

- `uv run pytest api/modules/order/tests/domain/test_payment_domain.py` -> 4 passed.
- `uv run pytest api/modules/order/tests/use_cases/test_create_payment_link_use_case.py` -> 7 passed.
- `uv run pytest api/modules/order/tests/domain api/modules/order/tests/use_cases` -> 43 passed, 4 pre-existing deprecation warnings for `datetime.utcnow()`.
- `uv run lint-imports` -> failed before analysis because package `modules` was not on `PYTHONPATH`.
- `$env:PYTHONPATH='api'; uv run lint-imports` -> payment-relevant layer/framework contracts kept; existing `No circular imports between apps` contract broken by pre-existing `infrastructure -> configuration` imports in catalog, config_coupon, conversation, and delivery.
- `uv run pytest api/modules/order/tests/integration/test_prisma_payment_repository.py` before implementation -> failed during collection with missing `PrismaPaymentRepository` import.
- `uv run prisma generate --schema api/shared/infrastructure/prisma/schema.prisma` -> passed and regenerated Prisma Client Python.
- `uv run pytest api/modules/order/tests/integration/test_prisma_payment_repository.py` after implementation -> collected 4 tests, all errored in setup because the shared Prisma fixture timed out connecting to Postgres at `localhost:5432`.
- `$env:PYTHONPATH='api'; uv run python -c "from modules.order.infrastructure.adapters.driven.prisma.payment_repository import PrismaPaymentRepository; print(PrismaPaymentRepository.__name__)"` -> passed.
- `uv run prisma validate --schema api/shared/infrastructure/prisma/schema.prisma` -> passed.

## Deviations

- Phase 3 uses `externalReference` as an index, not unique. The create-link use case currently uses `order_id` as the external reference, and unique would block later payment retries for the same order.
- DB-backed GREEN could not be confirmed because Postgres is unavailable in this environment. Code/schema validation passed, but the integration tests must be rerun with the DB service available.

## Remaining Next Task

- 4.1 RED: add Mercado Pago adapter tests for status mapping, settings/env defaults, SDK create/get calls, SDK error translation, and signature validation boundary.
- Before continuing deep infrastructure work, rerun `uv run pytest api/modules/order/tests/integration/test_prisma_payment_repository.py` with Postgres running to confirm Phase 3 GREEN.
