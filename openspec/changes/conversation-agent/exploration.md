# Exploration: Conversation Agent

## Current State (verified in code)

### `conversation`
- `configuration/container.py` -> `build_container()` wires **in-memory** repositories; `infrastructure/adapters/driven/prisma/*` exist but are unused.
- `PrismaConversationRepository.find_by_channel_identity` filters by `channel` + `clientId=None` because `Conversation` has **no external identity column**.
- `Conversation` has no `businessConfigId` -> no per-restaurant isolation.
- `ReceiveMessageUseCase` answers from a `DeterministicIntentDetector`; no LLM, no tools.
- `receive_message.py:63` uses `external_message_id or uuid4()` as the `Message` primary key.
- No `langchain`, `langgraph`, `langsmith` or LLM provider installed (`pyproject.toml`, site-packages).

### `order`
- Reusable driver ports exist: `StartDraftOrderUseCase`, `AddLineUseCase`, `UpdateLineQuantityUseCase` (quantity only), `RemoveLineUseCase`, `ConfigureOrderUseCase` (delivery + pickup via `delivery_type`), `ApplyCouponUseCase`, `ConfirmOrderUseCase`, `CancelOrderUseCase`, `GetOrderUseCase`, `ListOrdersUseCase`.
- `StartDraftOrderUseCase` always creates a new order (`id=uuid4()`); there is no read of the current draft.
- `OrderFilter` has only `status / delivery_type / payment_type / date_*` -> no `conversation_id`, `business_config_id` or `client_id`.
- `Order.conversationId` already exists in the schema, so conversation -> order association does not need a new link.
- `Order` has no `version`.
- `Order.confirm()` moves `DRAFT -> PENDING` and freezes prices; `can_be_modified()` requires `DRAFT`.
- Transition maps are **duplicated** in `advance_state_ports._ALLOWED_TRANSITIONS` and `update_order_status_use_case._ALLOWED_TRANSITIONS`.
- `CancelOrderUseCase._CANCELLABLE_STATES = {DRAFT, PENDING, PAID}` is missing `CONFIRMED` (RN-007 requires it).
- `PENDING -> CONFIRMED` (cash acceptance, RN-011 / RN-041 / REQ-042) is unreachable, and the backoffice panel advances status through `PATCH /api/orders/{id}/status/`.
- No idempotency mechanism exists.

### `order` payments
- `MercadoPagoPaymentProvider` uses the **Preferences API** (`sdk.preference().create`, `init_point`); the target is Checkout Pro + **Orders API** (`POST /v1/orders`).
- `PaymentProvider` exposes only `create_checkout_link` + `get_payment`; no cancel, no idempotency key.
- `Payment` has no `orderVersion`, no supersede/validity, no provider idempotency keys.
- `ProcessPaymentNotificationUseCase` sets `PENDING -> PAID` on `APPROVED` **without** validating version, amount or supersede.
- `Payment.preferenceId` is `@unique`; Orders API returns an order id, not a preference id.
- `AppliedCoupon` has no natural unique constraint on `(orderId, couponId)`.

### `delivery`
- `CalculateDeliveryQuotePort` already exists (`business_config_id`, `AddressInput`) and is already reused cross-module by `order` via `DeliveryQuoteAdapter`. This is the pattern to copy for `conversation`.

### `catalog`
- `ProductQueryUseCase` returns rich snapshots (variants, current price, ingredients with `removable`, modifier groups with `min/max` and `price_delta`).
- `ListProductsQuery` has `category_id` + `state`; **no `search`**.

## Constraints

- Hexagonal direction: `infrastructure -> application -> domain`.
- `domain` / `application` MUST NOT import `django`, `rest_framework`, `prisma`, `mercadopago`, `langchain`, `langgraph`, `langsmith`.
- Cross-module imports only through the sibling's `application.ports`.
- import-linter whitelist for `conversation` must apply **only** to `conversation/infrastructure/adapters`; `conversation/application` depends solely on its own ports.
- Prisma is the single source of truth for the data layer; migrations are additive where possible.

## Identity Model (decided)

```text
thread_id            -> Conversation.externalThreadId  (composite: businessConfigId + channel + externalThreadId)
incoming message     -> externalMessageId (stable, generated once per driver ingress) -> Message id / idempotency
run_id               -> LangSmith tracing only (never business idempotency)
Conversation.id      -> internal Rapidfood UUID (never equals thread_id)
```

## Affected Areas

- `api/modules/conversation/**` — application, infrastructure, configuration, tests.
- `api/modules/order/**` — domain, application, infrastructure, REST, tests.
- `api/modules/catalog/**` — list query + repository filter.
- `api/shared/infrastructure/prisma/schema.prisma` + migrations.
- `api/composition/container.py`, `pyproject.toml`, `api/config/settings.py`.
- `docs/order-state-machine.md`, `docs/reglas-negocio.md`.

## Ready for Proposal

Yes. All architectural decisions were closed with the user before writing this change; no open questions remain.
