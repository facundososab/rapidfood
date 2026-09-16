# Proposal: Mercado Pago Payments

## Problem Statement / Intent

Rapidfood must support online order payment via Mercado Pago while preserving hexagonal boundaries. Confirmed online orders currently can become `PENDING`, but there is no payment domain model/use case, provider port, Mercado Pago adapter, webhook processing, or REST payment endpoint to satisfy RN-038..RN-041 and REQ-047..REQ-051.

## Goals / Non-Goals

### In Scope
- Generate Mercado Pago Checkout Pro links for `ONLINE` orders in `PENDING`.
- Register each online payment attempt as local `Payment(PENDING)`.
- Process Mercado Pago notifications idempotently after fetching authoritative provider state.
- Move order `PENDING -> PAID` only when payment is approved.
- Expose REST endpoints for link creation and webhook receipt.
- Prepare, but not prioritize, WhatsApp conversation link delivery.

### Out of Scope
- Refunds, subscriptions, card capture, accounting reconciliation, admin payment panel, multiple providers.
- Conversation-first implementation before order payment flow and wiring are stable.

## Capabilities

### New Capabilities
- `order-payments`: order-owned online payment attempts, provider checkout link creation, webhook-driven payment status updates, and paid-order transition.

### Modified Capabilities
- `scaffold`: payment schema fields/import-contract expectations may need deltas because main specs still reference stale `apps/*` paths while actual code uses `api/modules/*`.

## Proposed Bounded-Context Approach

Keep payments inside the `order` bounded context for this increment. `Payment` belongs to the order checkout lifecycle; Mercado Pago is an infrastructure-only driven adapter behind an application `PaymentProvider` port. Driver REST adapters translate HTTP/webhook payloads to use-case commands. Composition stays explicit in `api/composition/container.py` and order configuration; no globals/service locator.

## User-Visible Behavior

- `POST /api/orders/{order_id}/payment-link/` returns `order_id`, `payment_id`, provider, `checkout_url`, and `PENDING` status.
- `POST /api/orders/payments/mercadopago/webhook/` receives provider notifications and returns quickly after delegating to use cases.
- WhatsApp can later send the link, explain the order remains pending, notify approval, or offer retry after rejection/failure/expiry.

## Impact

| Area | Impact |
|---|---|
| Domain | Add pure `Payment`/`PaymentStatus`; no Django/DRF/Prisma/Mercado Pago imports. |
| Application | Add DTOs, `PaymentRepository`, `PaymentProvider`, `CreatePaymentLinkUseCase`, `ProcessPaymentNotificationUseCase`. |
| Infrastructure | Add Prisma payment repository, Mercado Pago adapter/settings/status mapper, schema migration if designed. |
| API | Add order REST serializers/views/routes. |
| Conversation | Later add payment-link port and cross-module adapter only after order flow works. |
| Data model | Evaluate `preferenceId`, `checkoutUrl`, `externalReference`, `providerPayload`, `expiresAt`. |

## Risks

| Risk | Likelihood | Mitigation |
|---|---|---|
| Duplicate webhooks | High | Idempotency by external id/preference/reference; no state regression. |
| Untrusted webhook payload | High | Always query Mercado Pago through `PaymentProvider` before local mutation. |
| SDK leakage inward | Med | Keep SDK only under infrastructure; enforce with `uv run lint-imports`. |
| Conversation wiring instability | Med | Defer conversation integration until order payment endpoints pass tests. |

## Rollout / Phase Plan

1. Spec/design DTOs, status mapping, idempotency, schema delta, endpoint semantics.
2. Strict TDD: domain/contracts and payment use cases first.
3. Prisma persistence and Mercado Pago infrastructure adapter.
4. REST endpoints and webhook tests.
5. Conversation integration after stable order flow.

## Rollback Plan

Remove payment use cases, ports, adapters, routes, and wiring. Revert Prisma payment-field migration if applied and not yet depended on. Conversation changes, if later added, roll back independently behind its port.

## Acceptance Criteria

- [ ] Online `PENDING` order can generate and persist a Mercado Pago link/payment attempt.
- [ ] Approved remote payment updates local payment and moves order to `PAID`.
- [ ] Rejected/failed/expired payment leaves order `PENDING` and supports retry messaging.
- [ ] Webhook processing is idempotent and provider-authoritative.
- [ ] Domain/application import no Django, DRF, Prisma, or Mercado Pago.
- [ ] Later phases verify with `uv run pytest` and `uv run lint-imports`; no builds.
