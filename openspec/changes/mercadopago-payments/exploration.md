# Exploration: mercadopago-payments

## Current State

- `docs/mercadopago-payments-implementation-plan.md` is the reference plan for this change and is aligned with payment rules from `docs/reglas-negocio.md` RN-038..RN-041 and `docs/req-funcionales.md` REQ-047..REQ-051.
- The actual backend code currently lives under `api/modules/*`, not root `apps/*`. `docs/ARCHITECTURE-GUIDE.md`, `AGENTS.md`, Django settings, import-linter root package, and current imports all use `modules.*` / `api/modules/*`; `openspec/config.yaml` still contains stale `apps/*` wording in its context line.
- `api/shared/infrastructure/prisma/schema.prisma` already has `Order`, `Payment`, `PaymentType`, and `PaymentStatus` with `PENDING`, `APPROVED`, `REJECTED`, `FAILED`, `EXPIRED`. `Payment` currently stores `id`, `orderId`, `provider`, `externalId`, `status`, `amount`, `createdAt`, `updatedAt`; it does NOT yet store `preferenceId`, `checkoutUrl`, `externalReference`, `providerPayload`, or `expiresAt` suggested by the plan.
- The `order` bounded context has domain entities and use cases for the order lifecycle: `Order`, `OrderState`, `PaymentMethod`, `ConfirmOrderUseCase`, `AdvanceStateUseCase`, `UpdateOrderStatusUseCase`, and Prisma-backed `PrismaOrderRepository`.
- There is no domain `Payment` entity, no domain `PaymentStatus`, no `PaymentRepository` port, no `PaymentProvider` port, no payment use cases, no Mercado Pago adapter, and no payment REST endpoints yet.
- `ConfirmOrderUseCase` confirms only `DRAFT -> PENDING` and freezes line prices. Payment approval should be a separate use case that updates a `Payment` and moves the order `PENDING -> PAID` only when rules allow it.
- `AdvanceStateUseCase` and `UpdateOrderStatusUseCase` duplicate transition maps and differ: `AdvanceStateUseCase` only allows forward operational transitions, while `UpdateOrderStatusUseCase` also allows cancellation. Payment processing should not rely on REST/admin status updates; it should express the payment-specific invariant directly or via a dedicated order state method/use case.
- REST order adapters live at `api/modules/order/infrastructure/adapters/driver/rest/`; `api/config/urls.py` exposes them under `/api/orders/`.
- The app-level composition root is `api/composition/container.py`; order views call `composition.container.get_app_container()`. Order's module container currently constructs `PrismaOrderRepository` directly and accepts only an optional catalog query adapter.
- Conversation has `ReceiveMessageUseCase` and cross-module Protocols in `api/modules/conversation/application/ports/driven/cross_module.py`; there is no payment-link port yet. Its HTTP wiring (`api/modules/conversation/infrastructure/adapters/driver/rest/urls.py`) still builds an in-memory conversation container directly, so conversation/payment integration should be later than core order payment flow.
- Tests are colocated under `api/modules/**/tests` plus Prisma tests under `api/shared/infrastructure/prisma/tests`; `pyproject.toml` testpaths include those locations. Strict TDD is enabled for implementation phases, so each later SDD apply task must start with failing tests before code.

## Affected Areas

- `docs/mercadopago-payments-implementation-plan.md` — canonical implementation plan and phase outline.
- `docs/reglas-negocio.md` — RN-038..RN-041 payment invariants.
- `docs/req-funcionales.md` — REQ-047..REQ-051 functional payment requirements.
- `docs/order-state-machine.md` — `PENDING -> PAID` transition source.
- `docs/modelo-dominio.md` — payment belongs to order model relationship.
- `api/shared/infrastructure/prisma/schema.prisma` — existing `Payment` model/enums; likely needs fields for Mercado Pago preference/link/idempotency.
- `api/modules/order/domain/models/` — add pure `Payment` and `PaymentStatus`; keep Prisma enums out of domain.
- `api/modules/order/application/ports/driver/` — add command/response DTOs and driver ports for creating payment links and processing notifications.
- `api/modules/order/application/ports/driven/` — add `PaymentRepository` and provider capability port (`PaymentProvider`/`PaymentGateway`).
- `api/modules/order/application/use_cases/` — add `CreatePaymentLinkUseCase` and `ProcessPaymentNotificationUseCase`.
- `api/modules/order/infrastructure/adapters/driven/prisma/` — add `PrismaPaymentRepository`, preferably with mapper helpers if translation grows.
- `api/modules/order/infrastructure/adapters/driven/mercadopago/` — add Mercado Pago provider adapter, settings, status mapper, and webhook signature validation helper if configured.
- `api/modules/order/infrastructure/adapters/driver/rest/` — add serializers, views, and routes for payment-link creation and Mercado Pago webhook.
- `api/modules/order/configuration/container.py` and `api/composition/container.py` — wire payment repository/provider and new use cases explicitly; avoid hidden globals/service locators.
- `api/modules/order/tests/` — add TDD unit tests for domain/use cases, REST tests for endpoints, and optional Prisma integration tests.
- `api/modules/conversation/application/ports/driven/cross_module.py` and `api/modules/conversation/application/use_cases/receive_message.py` — later add a payment-link capability only after order payment flow is stable.

## Mismatches / Drift

- `openspec/config.yaml` still says architecture uses `apps/client`, `apps/conversation`, etc.; actual code and active docs use `api/modules/*` with imports rooted at `modules`.
- `openspec/config.yaml` says the Prisma test fixture lives in `tests/conftest.py`; actual fixture is `api/shared/infrastructure/prisma/tests/conftest.py` and `pyproject.toml` includes that path.
- Older SDD artifacts describe earlier scaffold drift around `apps/*`; current worktree has moved to `api/modules/*`. Future phases should not resurrect `apps/*` paths.
- The implementation plan suggests `POST /api/orders/{order_id}/payment-link/` and `POST /api/orders/payments/mercadopago/webhook/`; current URL style under `api/modules/order/infrastructure/adapters/driver/rest/urls.py` can support these as `<uuid:order_id>/payment-link/` and `payments/mercadopago/webhook/` under the existing `/api/orders/` include.
- `docs/ARCHITECTURE-GUIDE.md` section 8 discusses Django ORM mapper folders, but actual persistence adapters use Prisma Client Python and often inline mappers. For payments, follow the active Prisma adapter convention while keeping mapping inside infrastructure.

## Approaches

1. **Order-owned payment capability first (recommended)** — implement payments inside the `order` bounded context, with Mercado Pago as an outbound provider adapter and payment REST/webhook as driver adapters.
   - Pros: matches docs and existing `Order.payments` schema; minimal bounded-context sprawl; keeps payment approval tied to order state rules.
   - Cons: if refunds/reconciliation/multiple providers grow, this may later split into a dedicated payment bounded context.
   - Effort: Medium.

2. **New standalone `payment` module now** — introduce a separate bounded context for all payment behavior.
   - Pros: cleaner if payment domain becomes large and provider-agnostic.
   - Cons: premature complexity today; more cross-module contracts and wiring before a single provider flow exists.
   - Effort: High.

3. **Conversation-first integration** — add payment-link behavior directly into WhatsApp/conversation flow.
   - Pros: visible user-facing behavior sooner.
   - Cons: risks embedding provider/order rules in conversation; current conversation container uses memory repositories and incomplete real wiring.
   - Effort: High and risky.

## Recommendation

Use **Approach 1: order-owned payment capability first**. Treat `Payment` as part of the order checkout lifecycle aggregate boundary for this increment, model Mercado Pago behind an application port, and expose two order REST driver endpoints. Defer conversation integration until the order module can generate links and process webhooks deterministically.

Implementation-ready phase ordering for SDD:

1. **Spec/design**: define exact payment requirements/scenarios, DTOs, idempotency rules, status mapping, endpoint semantics, and schema delta.
2. **Domain/contracts**: add pure `Payment`, `PaymentStatus`, driver DTOs, `PaymentRepository`, `PaymentProvider`; tests first.
3. **Create link use case**: validate order exists, is `PENDING`, `payment_type == ONLINE`, and has a positive `total_amount`; create `PENDING` payment; call provider; persist provider identifiers/link; return plain response.
4. **Process notification use case**: accept normalized notification, query provider for authoritative payment data, update local payment idempotently, move order `PENDING -> PAID` only on approved status, leave rejected/failed/expired orders pending.
5. **Persistence**: update Prisma schema if approved by design, run Prisma generation/migration only in implementation phase, add `PrismaPaymentRepository` and integration tests.
6. **Mercado Pago adapter**: add SDK/dependency and env settings in infrastructure only; map provider statuses; keep SDK types out of application/domain.
7. **REST endpoints**: add serializers/views/routes under order REST adapter; validate webhook signature when configured and respond quickly.
8. **Conversation integration**: add a payment-link port to conversation and wire a cross-module adapter in app composition only, after conversation's real repository/container wiring is addressed.
9. **Verification**: run `uv run pytest` and `uv run lint-imports` in verify/apply phases; do not run builds.

## Risks

- Webhook idempotency is mandatory: Mercado Pago can retry notifications; local updates must not duplicate effects or regress an approved payment.
- Do not trust raw webhook payload status; always fetch the authoritative Mercado Pago resource through the provider port before changing local state.
- Existing `Payment` schema may be insufficient for Checkout Pro traceability/idempotency unless preference/link/reference fields are added.
- Conversation integration is currently unsafe as a first step because its URL module builds an in-memory container and does not use the app-level composition root.
- Adding Mercado Pago SDK must be isolated to infrastructure; importing it from domain/application would violate import-linter and project standards.
- Strict TDD applies to implementation phases; tests should drive use-case contracts before adapters.
- Avoid reusing `UpdateOrderStatusUseCase` as payment business logic; payment approval needs payment-specific rules and idempotency.

## Ready for Proposal

Yes. The next SDD phase should update/create proposal/spec/design for `mercadopago-payments`, anchored in `api/modules/order` as the initial bounded context and explicitly noting that `openspec/config.yaml` has stale `apps/*` wording while actual code uses `api/modules/*`.
