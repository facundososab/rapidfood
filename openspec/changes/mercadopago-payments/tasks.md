# Tasks: Mercado Pago Payments

Strict TDD: each RED task adds/records a failing focused `uv run pytest ...`; each GREEN task records the focused pass. Do not implement conversation integration until the order payment flow is stable.

## Phase 1: Domain and Test Scaffolding

- [x] 1.1 RED: add `api/modules/order/tests/domain/test_payment_domain.py` for `PaymentStatus` values, final statuses, and idempotency helpers.
- [x] 1.2 GREEN: create pure `domain/models/{payment_status.py,payment.py}` and export from `domain/models/__init__.py`.
- [x] 1.3 RED: add `api/modules/order/tests/use_cases/test_create_payment_link_use_case.py` fakes for missing/not-PENDING/not-ONLINE/non-positive orders.

## Phase 2: Application Ports and Link Use Case

- [x] 2.1 GREEN: add driver DTOs in `application/ports/driver/payment_ports.py` and driven ports `payment_repository.py`, `payment_provider.py`.
- [x] 2.2 RED: test payable order creates `Payment(PENDING)`, calls provider once, persists provider ids/link, returns plain result.
- [x] 2.3 GREEN: implement `application/use_cases/create_payment_link_use_case.py` with constructor-injected ports only.

## Phase 3: Prisma Persistence

- [x] 3.1 RED: add `api/modules/order/tests/integration/test_prisma_payment_repository.py` marked `db` for create, lookup by external/preference/reference, status update.
- [x] 3.2 GREEN: update `api/shared/infrastructure/prisma/schema.prisma` with payment trace fields/indexes; create migration and regenerate Prisma client.
- [x] 3.3 GREEN: implement `infrastructure/adapters/driven/prisma/{payment_repository.py,mappers/payment_mapper.py}`.

## Phase 4: Mercado Pago Adapter

- [ ] 4.1 RED: add adapter tests for status mapping, settings/env defaults, SDK create/get calls, SDK error translation, and signature validation boundary.
- [ ] 4.2 GREEN: add `mercadopago` via `uv`; implement `infrastructure/adapters/driven/mercadopago/{mercadopago_settings.py,mercadopago_status_mapper.py,mercadopago_payment_provider.py,errors.py}`.

## Phase 5: Webhook Use Case and Idempotency

- [ ] 5.1 RED: add `test_process_payment_notification_use_case.py` for provider-authoritative lookup before mutation, approved pays order, non-approved stays pending, duplicates no-op.
- [ ] 5.2 GREEN: implement `application/use_cases/process_payment_notification_use_case.py` using payment lookup by external id, preference id, or external reference.

## Phase 6: DRF Driver and Routes

- [ ] 6.1 RED: add REST tests for `POST /api/orders/{order_id}/payment-link/`, webhook success, invalid signature rejection, and views delegating only.
- [ ] 6.2 GREEN: update `rest/{serializers.py,views.py,urls.py}` with payment-link serializer/view and Mercado Pago webhook serializer/view/signature validator.

## Phase 7: Composition and Architecture Gate

- [ ] 7.1 RED: test `api/modules/order/configuration/container.py` exposes payment use cases wired explicitly.
- [ ] 7.2 GREEN: wire `PaymentRepository`, Mercado Pago provider, and use cases in order container and `api/composition/container.py`; no service locator.
- [ ] 7.3 Update `[tool.importlinter]` in `pyproject.toml`: fix actual driver/driven paths and forbid `mercadopago` in domain/application.

## Phase 8: Deferred Conversation Integration (later phase)

- [ ] 8.1 LATER: add conversation payment-link port/cross-module adapter only after phases 1-7 pass.
- [ ] 8.2 LATER: update WhatsApp confirm/retry/payment-approved copy and tests after real conversation wiring is stable.

## Phase 9: Verification

- [ ] 9.1 Run focused domain/use-case tests: `uv run pytest api/modules/order/tests/domain api/modules/order/tests/use_cases`.
- [ ] 9.2 Run focused adapter/REST tests: `uv run pytest api/modules/order/tests/integration api/modules/order/tests`.
- [ ] 9.3 Run final gates: `uv run pytest` and `uv run lint-imports`; do not run builds.
