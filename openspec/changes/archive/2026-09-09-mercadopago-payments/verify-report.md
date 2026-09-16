# Verification Report: Mercado Pago Payments

**Change**: mercadopago-payments
**Mode**: Strict TDD
**Project**: rapidfood
**Date**: 2026-09-09
**Verdict**: PASS WITH WARNINGS

## Executive Summary

Payment implementation conforms to the `order-payments` SDD spec and reference plan for phases 1-7. Runtime evidence is green for payment-specific tests and the full `api/modules/order/tests` package. Prisma schema validation is green. The payment-relevant architecture boundary is also green: domain/application/ports/use cases do not import Django, DRF, Prisma, or Mercado Pago, and Mercado Pago SDK usage is isolated in infrastructure.

Global `uv run pytest` and `uv run lint-imports` still fail, but the observed failures are outside the Mercado Pago payment implementation: catalog URL/container import mismatch, delivery tests/domain drift, config_coupon integration failures, and pre-existing architecture cycles/driver-container transitive edges.

## Artifacts Read

- Engram `sdd/mercadopago-payments/tasks` observation #752.
- Engram `sdd/mercadopago-payments/apply-progress` observation #757.
- Engram `sdd/mercadopago-payments/design` observation #749.
- Engram `sdd/mercadopago-payments/spec` observation #746.
- Engram `sdd/mercadopago-payments/proposal` observation #743.
- Engram `sdd/mercadopago-payments/explore` observation #740.
- `openspec/changes/mercadopago-payments/tasks.md`.
- `openspec/changes/mercadopago-payments/apply-progress.md`.
- `openspec/changes/mercadopago-payments/design.md`.
- `openspec/changes/mercadopago-payments/specs/order-payments/spec.md`.
- `openspec/changes/mercadopago-payments/specs/scaffold/spec.md`.
- `docs/mercadopago-payments-implementation-plan.md`.

## Completeness

| Metric | Value |
|--------|-------|
| Phases 1-7 implementation tasks | Complete |
| Deferred conversation tasks | Incomplete by design, later phase |
| Verification tasks | Executed in this report |

Incomplete non-blocking tasks:

- 8.1 LATER: add conversation payment-link port/cross-module adapter only after phases 1-7 pass.
- 8.2 LATER: update WhatsApp confirm/retry/payment-approved copy and tests after real conversation wiring is stable.
- 9.3 global final gates are still red due unrelated pre-existing failures outside payment.

## Spec Compliance Matrix

| Requirement | Scenario | Runtime Evidence | Result |
|-------------|----------|------------------|--------|
| Payment link creation | Create link for payable order | `api/modules/order/tests/use_cases/test_create_payment_link_use_case.py::test_payable_order_creates_pending_payment_and_persists_provider_link`; REST evidence in `test_payment_link_endpoint_delegates_to_use_case`; integration persistence in `test_save_provider_data_and_lookup_by_external_and_preference_ids` | COMPLIANT |
| Payment link creation | Reject invalid link creation | `test_rejects_missing_order_before_creating_provider_link`, `test_rejects_order_that_is_not_pending_before_creating_provider_link`, `test_rejects_non_online_order_before_creating_provider_link`, `test_rejects_non_positive_total_before_creating_provider_link` | COMPLIANT |
| Provider-authoritative notification processing | Authoritative lookup precedes mutation | `api/modules/order/tests/use_cases/test_process_payment_notification_use_case.py::test_fetches_authoritative_provider_payment_before_local_mutation`; raw payload status is kept only in command payload and not used for state | COMPLIANT |
| Provider-authoritative notification processing | Duplicate notification is idempotent | `test_duplicate_final_notification_is_idempotent_without_duplicate_effects`; `test_save_updates_existing_payment_without_creating_duplicates` | COMPLIANT |
| Payment status mapping and order transition | Approved payment pays order | `test_fetches_authoritative_provider_payment_before_local_mutation`; `test_get_payment_maps_sdk_response_to_provider_payment`; `test_update_status_persists_payment_status` | COMPLIANT |
| Payment status mapping and order transition | Non-approved payment keeps order pending | `test_non_approved_payment_updates_payment_and_keeps_order_pending` parametrized for REJECTED, FAILED, EXPIRED; mapper tests for rejected/cancelled/expired | COMPLIANT |
| REST and conversation boundaries | REST endpoints delegate to use cases | `api/modules/order/tests/infrastructure/test_payment_rest_views.py` verifies delegation, route registration, signature rejection before use case, and transport-safe response | COMPLIANT |
| REST and conversation boundaries | Deferred conversation messaging | Conversation wiring is explicitly deferred in tasks/design and was not required by this verify prompt. No runtime implementation expected in phases 1-7. | DEFERRED / NON-BLOCKING |
| Hexagonal payment architecture | Dependency direction is enforced | `$env:PYTHONPATH='api'; uv run lint-imports` keeps `Domain, ports and use cases must not import frameworks`; static grep confirms `mercadopago` import only in infrastructure/tests/configuration | COMPLIANT WITH GLOBAL WARNINGS |
| Scaffold | Modules import cleanly | `api/modules/order/tests` imports and runs green. Global Django URL import still fails through catalog `views_variants -> modules.catalog.configuration.container.get_app_catalog_container`, outside payment. | WARNING / UNRELATED GLOBAL FAILURE |
| Scaffold | Framework ban enforced | import-linter contract kept with `forbidden_modules = ["django", "rest_framework", "prisma", "mercadopago"]` for domain/application/ports/use cases | COMPLIANT |
| Scaffold | Port-only cross-module edge | No conversation payment edge implemented yet; design says defer. Existing cross-module port warnings are unmatched-ignore warnings, not payment violations. | DEFERRED / NON-BLOCKING |
| Scaffold | Payment provider isolation | `mercadopago` SDK imported only inside `MercadoPagoPaymentProvider.__init__` in infrastructure; import-linter framework/SDK ban kept | COMPLIANT |

Compliance summary: 10 compliant, 2 deferred/non-blocking, 1 unrelated global warning.

## Static Correctness Evidence

| Area | Status | Evidence |
|------|--------|----------|
| Domain purity | PASS | `Payment` and `PaymentStatus` only import stdlib/domain types. |
| Application purity | PASS | Payment use cases depend on order/payment ports and domain models only. No Django/DRF/Prisma/Mercado Pago imports. |
| Payment link invariants | PASS | `CreatePaymentLinkUseCase` checks order existence, `PENDING`, `ONLINE`, and positive total before creating local payment/provider link. |
| Pending Payment and provider identifiers | PASS | Local pending payment is created first, then provider `external_id`, `preference_id`, `checkout_url`, `external_reference` are persisted via repository `save`. |
| Authoritative webhook processing | PASS | `ProcessPaymentNotificationUseCase` calls `payment_provider.get_payment(command.data_id)` before local lookup/mutation. |
| Status mapping | PASS | Mercado Pago statuses map to domain `APPROVED`, `REJECTED`, `FAILED`, `EXPIRED`, and pending states. Unknown statuses fail closed to `FAILED`. |
| Order transition | PASS | Only `PaymentStatus.APPROVED` moves `OrderState.PENDING` to `OrderState.PAID`; non-approved statuses never save the order as paid. |
| Duplicate notification idempotency | PASS | Same final status short-circuits updates and repeated order saves. |
| REST boundary | PASS | Payment REST views validate protocol shape/signature and delegate to use cases. Serializers contain no business rules. |
| Mercado Pago SDK isolation | PASS | SDK import occurs only in `api/modules/order/infrastructure/adapters/driven/mercadopago/mercadopago_payment_provider.py`. |
| ARS default | PASS | `MercadoPagoSettings.currency` defaults to `ARS`; container and provider payload tests verify ARS. |
| Provider payload persistence | SUGGESTION | Prisma has `providerPayload`, but current mapper/repository does not populate it. The SDD acceptance focuses on identifiers/link, so this is not blocking. |

## Design Coherence

| Decision | Followed? | Notes |
|----------|-----------|-------|
| Keep payments in order bounded context | YES | Implemented under `api/modules/order`. |
| SDK only in infrastructure | YES | Application sees `PaymentProvider`; SDK import isolated in driven adapter. |
| Never trust raw webhook status | YES | Use case queries provider first and ignores raw payload status for mutation. |
| Conversation deferred | YES | Phase 8 remains intentionally incomplete. |
| Explicit composition root | YES WITH WARNING | `api/composition/container.py` builds `OrderContainer`; order module also has lazy module-level singleton. This matches existing pattern and avoids import-time env/DB side effects, but broader app architecture still has unrelated driver-container cycles. |

## Strict TDD Compliance

| Check | Result | Details |
|-------|--------|---------|
| TDD Evidence reported | PASS | `apply-progress.md` contains full TDD Cycle Evidence table. |
| All payment tasks have tests | PASS | Tasks 1.1 through 7.2 have concrete test files; 7.3 has import-linter evidence. |
| RED confirmed | PASS | Referenced test files exist and apply-progress records initial failing reasons. |
| GREEN confirmed | PASS | Focused payment suite passed 36/36 in this verify run. |
| Triangulation adequate | PASS | Invalid link creation, status matrix, lookup fallbacks, duplicate path, REST signature paths, and Prisma persistence have multiple cases. |
| Safety net for modified files | PASS WITH WARNING | Safety net evidence is present for existing migration/import-linter changes. Most payment files were new. |

## Test Layer Distribution

| Layer | Test Files | Runtime Outcome |
|-------|------------|-----------------|
| Unit/domain | `test_payment_domain.py` | Passed in focused suite and order suite. |
| Unit/application | `test_create_payment_link_use_case.py`, `test_process_payment_notification_use_case.py` | Passed in focused suite and order suite. |
| Unit/infrastructure REST/SDK | `test_mercadopago_adapter.py`, `test_payment_rest_views.py`, `test_order_container_payment_wiring.py` | Passed in focused suite and order suite. |
| Integration/Prisma | `test_prisma_payment_repository.py` | Passed against DB-backed Prisma fixture. |
| E2E | None | Not required for this phase. |

## Changed File Coverage

Coverage analysis skipped: `pytest-cov` is not installed and no coverage command/threshold is configured in `pyproject.toml`.

## Assertion Quality

Assertion quality: PASS. No tautologies, ghost loops, production-code-free tests, or smoke-only REST tests were found in the payment-related test files inspected. Some assertions check collaborator calls, but they verify required boundary delegation/idempotency behavior rather than internal implementation trivia.

## Quality Metrics

- Linter/type checker: no dedicated changed-file linter/type checker command configured beyond import-linter.
- Architecture gate: payment-relevant import-linter contracts kept; unrelated global architecture contracts remain broken.

## Verification Commands Run

| Command | Outcome |
|---------|---------|
| `uv run pytest api/modules/order/tests/domain/test_payment_domain.py api/modules/order/tests/use_cases/test_create_payment_link_use_case.py api/modules/order/tests/use_cases/test_process_payment_notification_use_case.py api/modules/order/tests/infrastructure/test_mercadopago_adapter.py api/modules/order/tests/infrastructure/test_payment_rest_views.py api/modules/order/tests/integration/test_prisma_payment_repository.py api/modules/order/tests/configuration/test_order_container_payment_wiring.py` | PASS: 36 passed in 11.15s. |
| `uv run prisma validate --schema api/shared/infrastructure/prisma/schema.prisma` | PASS: schema valid. |
| `$env:PYTHONPATH='api'; uv run lint-imports` | WARNING: 8 contracts kept, 2 broken. Payment-relevant framework/SDK ban kept. Broken contracts are unrelated driver-to-driven transitive edges and cycles in catalog, conversation, delivery, config_coupon. |
| `uv run pytest api/modules/order/tests` | PASS: 70 passed, 4 pre-existing `datetime.utcnow()` deprecation warnings in order tests. |
| `uv run pytest` | WARNING/UNRELATED GLOBAL FAILURE: 226 passed, 21 failed, 6 errors, 4 warnings. Failures observed in config_coupon integration, conversation/catalog URL import, delivery domain/use-case tests, and shared health smoke via catalog URL import. |
| `uv run python -c "import importlib.util; print('pytest-cov available' if importlib.util.find_spec('pytest_cov') else 'pytest-cov not installed')"` | INFO: pytest-cov not installed. |

## Findings

### CRITICAL

None for `mercadopago-payments` phases 1-7.

### WARNING

- Global `uv run pytest` fails outside payment: config_coupon Prisma integration, conversation tests blocked by catalog URL import, delivery domain/use-case drift, and shared health smoke blocked by catalog URL import.
- Global `uv run lint-imports` fails outside payment: driver adapters transitively import driven adapters through configuration containers in catalog/conversation/delivery, and app cycles exist in catalog/config_coupon/conversation/delivery.
- `api/modules/order` emits 4 pre-existing `datetime.utcnow()` deprecation warnings in non-payment order tests.
- `OrderContainer` requires `MERCADOPAGO_ACCESS_TOKEN` when built, so environments hitting app/container wiring must configure Mercado Pago even before conversation integration.

### SUGGESTION

- Decide whether `providerPayload` should be persisted from Mercado Pago responses. The schema supports it, but current payment code persists only identifiers/link/status. Not blocking because spec acceptance requires identifiers/link.
- When Phase 8 starts, add conversation payment-link port and retry/approval messaging tests rather than importing order infrastructure from conversation.

## Risks

- End-to-end Django URL resolution remains globally fragile because catalog REST imports a missing `get_app_catalog_container` from the catalog module container.
- Production/local runtime needs `MERCADOPAGO_ACCESS_TOKEN`; missing env will fail container construction.
- Real Mercado Pago webhook delivery was not manually tested through a public HTTPS tunnel; this was listed in the reference plan as manual verification, not part of the automated phase gate.
- `externalReference` intentionally remains indexed, not unique, to allow retries for the same order; lookup returns latest by `createdAt`.

## Next Recommended

1. Archive or accept `mercadopago-payments` phases 1-7 as passing with warnings.
2. Open/fix a separate scaffold/architecture cleanup change for global URL/import-linter failures.
3. Start Phase 8 conversation integration only after the global scaffold blockers are addressed or explicitly scoped around.
