# Archive Report: Mercado Pago Payments

## Status

Archived with `pass_with_warnings` for phases 1-7.

## Executive Summary

`mercadopago-payments` phases 1-7 are accepted as complete. Payment-focused tests passed, full order tests passed, Prisma schema validation passed, and the payment SDK/framework isolation rule remained enforced. Global pytest/import-linter warnings are preserved because they are unrelated to payment and belong to separate scaffold/architecture cleanup work. Conversation integration remains deferred by design.

## Artifacts Read

- Engram `sdd/mercadopago-payments/explore` observation #740.
- Engram `sdd/mercadopago-payments/proposal` observation #743.
- Engram `sdd/mercadopago-payments/spec` observation #746.
- Engram `sdd/mercadopago-payments/design` observation #749.
- Engram `sdd/mercadopago-payments/tasks` observation #752.
- Engram `sdd/mercadopago-payments/apply-progress` observation #757.
- Engram `sdd/mercadopago-payments/verify-report` observation #774.
- OpenSpec `openspec/changes/mercadopago-payments/exploration.md`.
- OpenSpec `openspec/changes/mercadopago-payments/proposal.md`.
- OpenSpec `openspec/changes/mercadopago-payments/design.md`.
- OpenSpec `openspec/changes/mercadopago-payments/tasks.md`.
- OpenSpec `openspec/changes/mercadopago-payments/apply-progress.md`.
- OpenSpec `openspec/changes/mercadopago-payments/verify-report.md`.
- OpenSpec `openspec/changes/mercadopago-payments/specs/order-payments/spec.md`.
- OpenSpec `openspec/changes/mercadopago-payments/specs/scaffold/spec.md`.

## Archived Scope

- Phase 1: payment domain and tests.
- Phase 2: payment application ports and create-link use case.
- Phase 3: Prisma payment persistence and schema trace fields.
- Phase 4: Mercado Pago driven adapter, settings, status mapper, and SDK isolation.
- Phase 5: provider-authoritative notification use case and idempotency.
- Phase 6: REST driver endpoints for payment links and webhooks.
- Phase 7: explicit order container wiring and payment import-linter constraints.

## Specs Synced

| Domain | Action | Details |
|---|---|---|
| `order-payments` | Created | New main spec copied from the accepted delta. |
| `scaffold` | Deferred merge | Existing scaffold spec has unrelated historical scenarios. The delta was not destructively merged to avoid erasing or overwriting unrelated scaffold requirements. |

## Warnings Preserved

- Global `uv run pytest` remains red outside payment: config_coupon Prisma integration, conversation/catalog URL import, delivery domain/use-case drift, and shared health smoke through catalog URL import.
- Global `uv run lint-imports` remains red outside payment: driver-container transitive edges and app cycles in catalog, conversation, delivery, and config_coupon.
- `api/modules/order` has pre-existing `datetime.utcnow()` deprecation warnings in non-payment order tests.
- `OrderContainer` requires `MERCADOPAGO_ACCESS_TOKEN` when built.
- `providerPayload` exists in Prisma schema but is not yet populated by the current payment repository/mapper.
- Phase 8 conversation payment-link messaging remains deferred.

## Next Recommended

1. Open a separate scaffold/architecture cleanup change for global URL/import-linter failures.
2. Start Phase 8 conversation integration only after global scaffold blockers are fixed or explicitly scoped around.
3. Decide whether Mercado Pago `providerPayload` should be persisted from provider responses.

## Risks

- Real Mercado Pago webhook delivery was not manually tested through a public HTTPS tunnel.
- Missing `MERCADOPAGO_ACCESS_TOKEN` can break runtime container construction for payment endpoints.
- The accepted `scaffold` delta is traceable in the archived change but not merged into the main scaffold spec.
