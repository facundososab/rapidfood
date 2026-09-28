# Proposal: Conversation Agent (LangChain + LangGraph, test driver LangSmith)

## Problem Statement / Intent

The `conversation` bounded context currently contains a deterministic intent scaffold with in-memory repositories (`configuration/container.py` -> `build_container()`), a non-functional external identity lookup, and no LLM. Rapidfood needs a real conversational agent that can answer catalog questions and build/confirm an order for a customer, while keeping hexagonal boundaries and keeping `order` as the sole owner of cart and payment rules.

This change supersedes the agent portion of the previous `conversations` change (which delivered the deterministic scaffold).

The first executable driver is LangSmith / LangGraph Studio. WhatsApp is explicitly out of scope, but the application layer MUST NOT be designed around LangSmith.

## Goals / Non-Goals

### In Scope
- `conversation` application layer: `AgentExecutionContext`, driven ports `CatalogServicePort` / `OrderServicePort` / `DeliveryServicePort`, agent use cases, business/technical error mapping, thread -> conversation resolution, message persistence (USER then ASSISTANT).
- `conversation` infrastructure: cross-module adapters that call the public driver ports of `catalog`, `order`, `delivery`; explicit DI in `api/composition/container.py`. No internal HTTP.
- LangChain driver adapter + LangGraph graph exposed to Studio, thin tools, versioned system prompt, LangSmith tracing.
- `order` completion: `Order.version`, explicit `reopen_for_modification()` (PENDING -> DRAFT), centralized state-transition rules (single source of truth), CASH `PENDING -> CONFIRMED` fix, cancellation alignment with RN-007, `resolve_order_for_modification`, pure `get_current_order`, latest-active order, payment type, pickup, summary with `missing_requirements`, idempotent confirm/cancel.
- `order` payments reworked as `PaymentAttempt` on Mercado Pago **Checkout Pro + Orders API** with `X-Idempotency-Key`, separate create/cancel keys, `supersededAt` separated from `providerStatus`, version/amount/superseded validation in the webhook, post-commit remote cancellation.
- `order` idempotency: neutral `IdempotentOperation` (businessConfigId + idempotencyKey unique), claimed atomically with the mutation in one PostgreSQL transaction.
- `catalog`: `search` filter on the product listing.
- Schema + migrations, import-linter contracts, settings/env.

### Out of Scope
- WhatsApp / Evolution API / Meta API / Chatwoot.
- A separate `payment` bounded context, `PaymentServicePort` in `conversation`, Outbox, Saga, Redis, distributed locks, message brokers, new microservices.
- Backoffice CRUD as agent tools (`create_product`, `advance_order`, `set_order_status`, `create_coupon`, delivery-zone config, etc.).
- `ForceCancelOrder` (exceptional admin cancellation after preparation).
- Admin UI changes.

## Capabilities

### New Capabilities
- `conversation-agent`: agent execution context, agent tool surface and policies, conversation thread resolution, message persistence, cross-module orchestration, no LLM-trusted business data.
- `order-lifecycle`: order versioning, explicit reopen (PENDING -> DRAFT), centralized state transitions, CASH acceptance, reopen-aware mutations, pure current-order resolution.
- `order-idempotency`: neutral, atomic operation idempotency for non-naturally-idempotent mutations.
- `catalog-query`: product search filter used by the agent.

### Modified Capabilities
- `order-payments`: switch Checkout Pro from Preferences API to Orders API; `PaymentAttempt` semantics with `orderVersion`, separate create/cancel idempotency keys, `supersededAt` separated from `providerStatus`, webhook validation by version/amount/superseded, post-commit remote cancellation.

## Proposed Bounded-Context Approach

```text
LangSmith / Studio            (test driver)
        |
LangGraph graph + LangChain tools   (conversation/infrastructure/adapters/driver/langchain)
        |
conversation application use cases  (conversation/application)
        |
CatalogServicePort | OrderServicePort | DeliveryServicePort   (conversation/application/ports/driven)
        |
conversation cross-module adapters  (conversation/infrastructure/adapters/driven)
        |
catalog / order / delivery public application ports
```

- LangChain lives only in `conversation/infrastructure`; `domain` and `application` MUST NOT import `langchain`, `langgraph`, `langsmith`, `django` or `prisma`.
- LangChain is a **driver adapter**. Tools are thin: tool input -> command -> conversation use case -> serialized result.
- Delivery quote reuses the existing `CalculateDeliveryQuotePort`; no second pricing engine.
- Payments stay inside `order`. `conversation` only sees `OrderServicePort`.
- Cross-module calls are in-process adapter calls, never HTTP.

## User-Visible Behavior

- From LangSmith/Studio, a conversation can: browse the menu, check variants/prices/ingredients/modifiers, start a draft, add/update/remove items, quote and set delivery, set pickup, set payment type, apply a coupon, get the summary, confirm explicitly, cancel when allowed, and query the latest active order.
- Confirmation is only executed after the backend summary is shown and the user explicitly confirms that summary.
- Informational questions never create a draft. Concrete purchase intent does.
- The current order may be `PENDING` with a pending online checkout; a new modification reopens it to `DRAFT`, supersedes the previous attempt, and requires a new explicit confirmation before a new checkout.

## Impact

| Area | Impact |
|---|---|
| `api/modules/conversation` | New application ports/use cases, cross-module adapters, LangChain driver, real composition root |
| `api/modules/order` | Versioning, reopen, centralized transitions, CASH fix, cancellation alignment, idempotency, PaymentAttempt + Orders API, new use cases + endpoints |
| `api/modules/catalog` | `search` filter on list products |
| `api/modules/delivery` | None (only reused by `conversation`) |
| `api/shared/infrastructure/prisma/schema.prisma` | Conversation identity/business, Order.version, PaymentAttempt fields, IdempotentOperation |
| `api/composition/container.py`, `pyproject.toml`, `api/config/settings.py` | Wiring, deps, import-linter, env |
| `docs/order-state-machine.md`, `docs/reglas-negocio.md` | Reconcile documented state machine with the implemented graph |

## Risks

| Risk | Likelihood | Mitigation |
|---|---|---|
| LLM invents prices/availability/status | High | Every dynamic value comes from a tool; prompt policy forbids inventing; tools never accept prices |
| Draft duplicated per turn | High | `conversation` resolves the current order; creation reuses `StartDraftOrderUseCase`; no per-turn create |
| Tool retries duplicate mutations | Med | `IdempotentOperation` claimed atomically with the mutation; semantic idempotency for confirm/cancel |
| Old checkout pays the current version | Med | Webhook validates `orderVersion` + `amount` + `not superseded`; remote cancel is best-effort only |
| State-machine drift (CASH unreachable) | High | Centralize transitions in `order/domain`; CASH fix + tests in this change |
| LangChain leaks inward | Med | import-linter forbidden modules + whitelist limited to `conversation.infrastructure.adapters` |
| Groq tool-calling variability | Med | Model configurable via env; model choice validated during apply |

## Rollout / Phase Plan

| Phase | Content |
|---|---|
| 0 | Deps, import-linter, schema + migrations, settings/env |
| 1 | Order core: version, reopen, IdempotentOperation (transactional), centralized transitions + CASH + cancellation |
| 2 | PaymentAttempt + Mercado Pago Orders API adapter + validated webhook + create/cancel checkout |
| 3 | Order: payment type, pickup, `get_current_order`, `resolve_order_for_modification`, summary, latest-active, idempotent confirm/cancel, endpoints |
| 4 | Catalog search |
| 5 | Conversation application: ports, DTOs, use cases, thread resolution |
| 6 | Conversation infrastructure: cross-module adapters + wiring |
| 7 | LangChain driver + tools + prompt + LangGraph/LangSmith runner |
| 8 | Tests, gates, docs, final report |

## Rollback Plan

- Each phase is a separate commit; revert in reverse order.
- Schema migrations are additive (new nullable columns + new table) except `Conversation.businessConfigId` becoming required after backfill; rollback of that step is `DROP NOT NULL` + drop column.
- The previous deterministic conversation behavior can be restored by reverting phases 5-7 without touching `order`.
- `order-payments` rollback: the Orders API adapter and `PaymentAttempt` fields are additive; the previous Preferences-based link flow can be restored by reverting phase 2 while keeping schema columns unused.

## Success Criteria

- [ ] LangChain/LangGraph/LangSmith imported only under `conversation/infrastructure`; import-linter green.
- [ ] All 15 tools exposed and tested; administrative operations absent.
- [ ] Informational questions never create a draft; second `add_item` reuses the same draft.
- [ ] No price/total/discount/shipping value is ever accepted from the LLM.
- [ ] Checkout creation and order mutation are safe under retry and concurrency.
- [ ] Webhook never pays an order when `orderVersion != Order.version`, amount mismatches, or the attempt is superseded.
- [ ] CASH and ONLINE both reach a coherent, reachable state machine.
- [ ] `uv run pytest` and `uv run import-linter lint` green.
