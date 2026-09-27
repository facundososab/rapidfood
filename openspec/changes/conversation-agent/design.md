# Design: Conversation Agent

## Technical Approach

`conversation` orchestrates. It never computes prices, discounts, shipping, coupon validity, variant/modifier/ingredient validity, order transitions, geocoding or routing. Those stay in `catalog`, `order`, `delivery` and `config_coupon`. The agent is a LangChain **driver adapter** running on LangGraph, exercised from LangSmith/Studio; the application layer stays framework-free.

## Architecture Decisions

| Decision | Choice | Alternatives / tradeoff | Rationale |
|---|---|---|---|
| LangChain placement | `conversation/infrastructure/adapters/driver/langchain/` | In application (rejected) | Keeps `application`/`domain` framework-free; enforced by import-linter |
| LangSmith role | Test driver + tracing only, separated from the LangChain adapter | Single `LangSmithLangChainAgent` class (rejected) | Studio sends messages/threads; LangChain interprets and calls tools |
| LLM runtime | LangGraph + Groq provider (`langchain-groq`), model via `AGENT_MODEL` | OpenAI/Anthropic | User already uses LangGraph; provider is swappable; tool-calling depends on the model so it is configurable |
| Cross-module integration | In-process adapters calling public driver ports | Internal HTTP (rejected) | Same process; keeps REST as public API only |
| Delivery quote | Reuse `CalculateDeliveryQuotePort` | New pricing engine (rejected) | Existing port is the source of truth |
| Payment ownership | Payments stay inside `order` (`Order`, `PaymentAttempt`, Mercado Pago adapter) | Separate `payment` context (rejected) | Payment exists only to charge an `Order`; versioning must be transactional with order mutation |
| Agent port for payments | `OrderServicePort` only, including `create_payment_checkout` | `PaymentServicePort` in conversation (rejected) | No new boundary needed now |
| Cart source of truth | `Order DRAFT` | LLM memory / conversation history (rejected) | Deterministic and auditable |
| Order identity in chat | `Order.conversationId` (already in schema) | New link table (rejected) | Already exists |
| External identity | `@@unique([businessConfigId, channel, externalThreadId])`; internal `Conversation.id` stays a Rapidfood UUID | `thread_id == conversation_id` (rejected) | Channel identity decoupled from internal identity so WhatsApp can replace LangSmith |
| Message identity | Stable `externalMessageId` per ingress, generated once by the driver | `run_id` (rejected: changes per retry); `thread_id` (rejected: PK collision) | Message-level idempotency |
| Editable invariant | `modificable ⇔ status == DRAFT`; explicit `reopen_for_modification()` PENDING -> DRAFT | Relax `can_be_modified()` (rejected) | PENDING means a confirmed, immutable snapshot |
| State machine | Centralized in `order/domain`, single source of truth | Duplicated maps (rejected) | Removes drift; fixes CASH |
| Idempotency concept | Neutral `IdempotentOperation`, unique `(businessConfigId, idempotencyKey)` | `AgentOperationKey` (rejected: channel-coupled) | Works for LangChain, WhatsApp, HTTP, future channels |
| Idempotency atomicity | Claim + mutation + persist result in **one** PostgreSQL transaction | Separate insert/commit (rejected) | No inconsistent intermediate state |
| Confirm/cancel idempotency | Semantic, by state | `IdempotentOperation` (unneeded) | Naturally idempotent domain operations |
| Remote checkout cancel | Best-effort after commit; retryable independently | Outbox / Saga / distributed locks (rejected) | Local consistency does not depend on the external call |
| Webhook authority | Validate `orderVersion` + `amount` + `not superseded` before any order transition | Trust provider APPROVED blindly (rejected) | An old checkout must never pay the current version |

## Data Flow

### Incoming message

```text
driver (LangSmith/Studio)
  -> resolve AgentExecutionContext (business_config_id, conversation_id, client_id, channel, external_thread_id)
  -> persist USER Message (externalMessageId, stable per ingress)
  -> LangChainConversationAgentAdapter (LangGraph graph)
       0..N tool calls -> conversation use case -> driven port -> cross-module adapter -> other context
  -> persist ASSISTANT Message
  -> return response
```

### Order mutation with reopen (atomic)

```mermaid
sequenceDiagram
    participant T as Tool (add_item)
    participant C as ConversationUseCase
    participant O as OrderServicePort
    participant R as Order/IdempotentOperation (1 tx)
    T->>C: execute(command + context)
    C->>O: mutate_current_order(business, conversation, externalMessageId, operation, args)
    O->>R: BEGIN; claim idempotency key; SELECT order FOR UPDATE
    alt order is DRAFT
        R->>R: apply mutation
    else PENDING + ONLINE + no current APPROVED attempt
        R->>R: reopen_for_modification(); supersede current PaymentAttempt; apply mutation
    else not editable
        R-->>O: CURRENT_ORDER_NOT_EDITABLE / NEW_ORDER_REQUIRED (no change)
    end
    R->>R: version++; persist result; COMMIT
    O-->>C: result (replayed if key already exists)
    C-->>T: serialized result
    Note over O: after COMMIT (best effort): POST /v1/orders/{id}/cancel for the superseded checkout
```

### Checkout creation

```mermaid
sequenceDiagram
    participant T as Tool (create_payment_checkout)
    participant C as ConversationUseCase
    participant O as OrderServicePort
    participant R as Order tx
    participant MP as MercadoPago Orders API
    T->>C: execute(context)
    C->>O: create_checkout(order_id, externalMessageId)
    O->>R: BEGIN; claim key; ensure current version; get/create PaymentAttempt; persist createIdempotencyKey; COMMIT
    O->>MP: POST /v1/orders (X-Idempotency-Key = createIdempotencyKey)
    MP-->>O: externalId + checkout_url (or timeout)
    O->>R: persist externalId/checkoutUrl/providerStatus
    O-->>C: checkout_url
```

### Webhook validation

```mermaid
sequenceDiagram
    participant MP as MercadoPago
    participant V as HTTP adapter
    participant U as HandlePaymentWebhookUseCase
    participant DB as PaymentAttempt + Order
    MP->>V: notification
    V->>U: command(external id, raw payload)
    U->>MP: fetch authoritative provider state
    U->>DB: find PaymentAttempt by (provider, externalId)
    alt APPROVED and orderVersion == order.version and amount matches and not superseded
        U->>DB: Order -> PAID
    else APPROVED but stale/superseded/mismatched
        U->>DB: payment attempt providerStatus = APPROVED; Order unchanged (kept for refund/reconciliation)
    else other status
        U->>DB: store mapped providerStatus; Order unchanged
    end
```

## Interfaces / Contracts

### `conversation` application

- `AgentExecutionContext`: `business_configuration_id`, `conversation_id`, `client_id`, `channel`, `external_thread_id?`. Resolved before tools run; never supplied by the model.
- `CatalogServicePort`: `search_products(business, query?, category?)`, `get_product_detail(business, product_id)` -> conversation-owned DTOs.
- `OrderServicePort`: `get_current_order`, `resolve_order_for_modification`, `add_line`, `update_line`, `remove_line`, `set_delivery`, `set_pickup`, `set_payment_type`, `apply_coupon`, `get_order_summary`, `get_latest_active_order`, `confirm_order`, `cancel_order`, `create_payment_checkout`.
- `DeliveryServicePort`: `quote_delivery(business, destination_address)`.
- Tool results are structured: business outcomes (`DELIVERY_OUTSIDE_ZONE`, `INVALID_COUPON`, `ORDER_NOT_CANCELLABLE`, `CURRENT_ORDER_NOT_EDITABLE`, ...) vs technical failures (`DELIVERY_PROVIDER_ERROR`). Technical errors never surface as business messages.
- Every write command carries the idempotency inputs: `externalMessageId`, `operationName`, canonical args.

### `order`

- `Order.version` monotonic; incremented by every mutation that changes the commercial snapshot (add/update/remove item, coupon, delivery address affecting shipping, DELIVERY <-> PICKUP).
- `Order.reopen_for_modification()`: `PENDING -> DRAFT`, only when `paymentType == ONLINE` and no `PaymentAttempt` with `orderVersion == order.version`, `providerStatus == APPROVED`, `superseded == false`; clears `confirmedAt`.
- Centralized transition rules (allowed set + payment-type conditions + cancellation set), consumed by `ConfirmOrderUseCase`, `CancelOrderUseCase`, `AdvanceStateUseCase`, `UpdateOrderStatusUseCase`.
- `get_current_order` returns `{order, editable, requiresReopenForModification, requiresNewOrder}` **without** mutating.
- `resolve_order_for_modification` returns `DRAFT | REOPENED | CURRENT_ORDER_NOT_EDITABLE | NEW_ORDER_REQUIRED` and never creates an order.

### Tool surface (15)

`search_products`, `get_product_detail`, `get_current_order`, `add_item`, `update_item`, `remove_item`, `quote_delivery`, `set_delivery`, `set_pickup`, `set_payment_type`, `apply_coupon`, `get_order_summary`, `confirm_order`, `cancel_order`, `get_latest_active_order`.

Explicitly NOT exposed: product/variant/price/ingredient/modifier CRUD, delivery zone/pricing config, `advance_order`, `set_order_status`, `create_coupon`, `reopen_order`.

### Prompt policies (versioned, infrastructure)

Never invent products, availability, prices, ingredients, modifier options, coupon validity, delivery availability, shipping costs, order totals or order status. Use tools for any state-dependent value. The backend `DRAFT` is the cart source of truth; conversation history is not. Only call `confirm_order` after presenting an up-to-date summary and receiving explicit confirmation of that summary.

## Testing Strategy

| Layer | Approach |
|---|---|
| Domain | `order` transitions, reopen, version, PaymentAttempt validity/supersede as pure tests |
| Application | Conversation use cases with fake ports; order mutation use cases with fake repos + a fake transaction that proves claim+mutation atomicity |
| Tools | Mock the use case; assert argument mapping, context injection (model cannot override ids), command mapping, result/error serialization; no DB |
| Idempotency | Same `externalMessageId` + same `add_item` -> one line; different message + same args -> two lines; same message, different `operationName` -> no collision; concurrent same key -> one mutation |
| Payments | Checkout version/supersede, cancel success/already-cancelled/cannot-cancel/timeout, stale APPROVED webhook, current-version wrong amount, create timeout retry reuses the same MP idempotency key |
| REST | Order/catalog endpoints, including version/summary fields |
| Architecture | import-linter (frameworks forbidden inward; whitelist only `conversation.infrastructure.adapters`) |
| Agent policy | LangSmith evaluation scenarios when credentials are available; otherwise documented scenarios |

## Migration / Rollout

1. Schema: add `Conversation.externalThreadId` (nullable) + `Conversation.businessConfigId` (nullable), backfill from the single business configuration, then make `businessConfigId` required and add `@@unique([businessConfigId, channel, externalThreadId])`.
2. Add `Order.version Int @default(0)`.
3. Extend `Payment` (table name kept): `orderVersion`, `supersededAt`, `cancellationStatus`, `createIdempotencyKey`, `cancelIdempotencyKey`; relax `preferenceId` uniqueness; add `@@unique([provider, externalId])`.
4. Add `IdempotentOperation` with `@@unique([businessConfigId, idempotencyKey])`.
5. Additions are additive except the `NOT NULL` step after backfill.

## Open Questions

None. All decisions were closed with the user; the only procedural dependency is exiting plan mode.
