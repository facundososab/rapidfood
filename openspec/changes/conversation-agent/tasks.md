# Tasks: Conversation Agent

Strict TDD: every RED task records a failing focused `uv run pytest ...`; every GREEN task records the focused pass. Gates per phase: `uv run pytest`, `uv run import-linter lint --config ../pyproject.toml`. No HTTP between bounded contexts.

## Phase 0: Foundations

- [x] 0.1 RED: add an architecture test/import assertion that `conversation.domain` and `conversation.application` import no `langchain`, `langgraph`, `langsmith`, `django`, `prisma`. — satisfied by the import-linter framework contract (the project's documented gate) instead of a redundant pytest.
- [x] 0.2 GREEN: add deps `langgraph`, `langchain-groq`, `langsmith`, `langchain-core` via `uv`.
- [x] 0.3 GREEN: extend import-linter: add `langchain`, `langgraph`, `langsmith` to the forbidden-frameworks contract; narrow the `conversation` whitelist to `modules.conversation.infrastructure.adapters.** -> modules.<sibling>.application.ports.**`; add `modules.delivery` to the whitelist.
- [x] 0.4 GREEN: schema + migration — `Conversation.externalThreadId`, `Conversation.businessConfigId` (backfill then required), `@@unique([businessConfigId, channel, externalThreadId])`; regenerate Prisma client.
- [x] 0.5 GREEN: settings/env — `GROQ_API_KEY`, `LANGCHAIN_API_KEY`, `LANGCHAIN_TRACING_V2`, `LANGCHAIN_PROJECT`, `AGENT_BUSINESS_CONFIG_ID`, `AGENT_MODEL`.
- [x] 0.6 Verify: `uv run prisma validate`, `uv run pytest`, `uv run import-linter lint`. — pytest 287 passed; import-linter 10/10; prisma valid. Required repairing two pre-existing defects first (see apply-progress): the non-replayable migration history and the out-of-scope Prisma `db` fixture.

## Phase 1: Order Core (version, reopen, transitions, idempotency)

- [x] 1.1 RED: centralize-transition tests in `api/modules/order/tests/domain/test_order_state_transitions.py` — allowed sets per payment type, `PENDING -> PAID` only ONLINE, `PENDING -> CONFIRMED` only CASH, cancellable only `{DRAFT, PENDING, PAID, CONFIRMED}`.
- [x] 1.2 GREEN: add `order/domain/services/state_transitions.py` and make `ConfirmOrderUseCase`, `CancelOrderUseCase`, `AdvanceStateUseCase`, `UpdateOrderStatusUseCase` delegate; removed the admin `IN_PREPARATION/READY -> CANCELLED` exception.
- [x] 1.3 RED: `Order.version` + `reopen_for_modification()` tests in `api/modules/order/tests/domain/test_order_version_and_reopen.py`.
- [x] 1.4 GREEN: implement `Order.version`, `reopen_for_modification()` (clears `confirmedAt`), version bumps on add/remove line and delivery changes; persist `version` in the Prisma mapper.
- [x] 1.5 RED: `IdempotentOperation` tests — canonical key derivation (`tests/use_cases/test_idempotency_key.py`) and the atomic executor (`tests/integration/test_idempotent_order_mutation.py`): replay returns the stored result without re-executing, distinct keys apply separately.
- [x] 1.6 GREEN: `IdempotentOperation` driven port (`application/ports/driven/idempotency.py`) + Prisma executor (`infrastructure/.../prisma/idempotent_order_mutation.py`) with a single transaction: order row lock (`SELECT ... FOR UPDATE`), claim, mutate, persist order + result, commit.
- [x] 1.7 RED: `resolve_order_for_modification` tests — readiness matrix + `prepare_order_for_modification` (`tests/use_cases/test_order_modification.py`): DRAFT keeps editable; PENDING+ONLINE reopens+supersedes; PENDING+CASH / PAID / CONFIRMED / terminal return `NEW_ORDER_REQUIRED` **without touching the order**.
- [x] 1.8 GREEN: implemented `application/order_modification.py` (`modification_readiness` pure read + `prepare_order_for_modification`), `PaymentAttemptQueryPort` + Prisma adapter, a tx-bound `AppliedCouponRepositoryPort` in the mutation context, and the reopen-aware idempotent mutations: `AddItemToOrderUseCase`, `UpdateItemInOrderUseCase` (quantity + modifiers + removed ingredients, repriced), `RemoveItemFromOrderUseCase`, `SetDeliveryForOrderUseCase` (quote resolved BEFORE the transaction; unavailable address never mutates) and `ApplyCouponToOrderUseCase` (validation + discount from `config_coupon`; applied-coupon history written in the same transaction). All wired in `OrderContainer` with unit tests. (`set_pickup` remains in Phase 3.)
- [x] 1.9 Verify: order domain + use-case suites green (full suite 328 passed).

## Phase 2: PaymentAttempt + Mercado Pago Orders API

- [x] 2.1 RED: `PaymentAttempt` domain tests — `providerStatus` separate from `supersededAt`; `CancellationStatus` lifecycle; superseded + APPROVED coexist; `is_current_for(version)`. (`domain/models/payment_attempt.py`, `domain/models/cancellation_status.py`, `tests/domain/test_payment_domain.py`.)
- [x] 2.2 GREEN: renamed the domain model `Payment` -> `PaymentAttempt` (Prisma table `payment` kept) with `order_version`, `superseded_at`, `cancellation_status`, `create_idempotency_key`, `cancel_idempotency_key`; new mapper `payment_attempt_mapper.py`; port renamed to `PaymentAttemptRepository` with `create_for_version` + `find_current_for_version`; Prisma repository persists the new fields. (Schema/migration already landed in Phase 0.)
- [x] 2.3 RED: `PaymentProviderPort` tests — `create_checkout` and `cancel_checkout` send **separate** stable `X-Idempotency-Key`s; retry reuses the same key; `already cancelled` maps to idempotent success (404/409); transport errors become technical errors (`tests/infrastructure/test_mercadopago_adapter.py`).
- [x] 2.4 GREEN: reworked the provider port (`create_checkout`, `cancel_checkout`, `get_payment`; the error moved to the port so use cases never import infra) and rewrote the Mercado Pago adapter to **Orders API** (`POST /v1/orders`, `POST /v1/orders/{id}/cancel`, `GET /v1/orders/{id}`) using `requests` with an injectable session.
- [x] 2.5/2.6 `CreatePaymentCheckoutUseCase`: validates PENDING/ONLINE/positive total, reuses the single logical attempt per version, persists the provider key BEFORE the remote call, replays when a checkout already exists, and reuses the same key on timeout retry. Replaces the deleted legacy `CreatePaymentLinkUseCase`.
- [x] 2.7/2.8 `HandlePaymentWebhookUseCase`: always fetches authoritative provider state, resolves the attempt by `(provider, externalId)`, persists the provider status even for a stale attempt, and pays the order only when the attempt matches the order's current version, the amount matches and it is not superseded. Replaces the deleted `ProcessPaymentNotificationUseCase`.
- [x] 2.9/2.10 `CancelSupersededCheckoutUseCase`: retries the remote cancellation independently with the persisted key, marks CANCELLED / REMOTE_ALREADY_CANCELLED / FAILED and never touches the order. `prepare_order_for_modification` now returns the superseded attempt ids and the mutation outcome exposes them so the caller can cancel AFTER the commit.
- [x] 2.11 Verify: full suite green (372 passed); import-linter 10/10.

## Phase 3: Order Completion + REST

- [ ] 3.1 RED: `get_current_order` pure-read matrix tests (DRAFT / PENDING+ONLINE / PENDING+CASH / PAID-CONFIRMED-IN_PREPARATION-READY-DELIVERED-PICKED_UP / APPROVED current / CANCELLED) — no state change.
- [ ] 3.2 GREEN: implement `get_current_order` (pure) and `get_latest_active_order` (business + client + conversation scope).
- [~] 3.3 RED: tests for `set_payment_type` (CASH/ONLINE only), `set_pickup`, `get_order_summary` (`subtotal`, `discount`, `shipping_cost`, `total_amount`, `delivery_type`, `address`, `payment_type`, `missing_requirements`), idempotent `confirm` retry, idempotent `cancel` retry. — `set_payment_type` done: `SetPaymentTypeUseCase` + `PATCH /api/orders/{id}/payment-type/` + tests + POS now persists it.
- [x] 3.4 GREEN: implemented `SetPickupForOrderUseCase` (reopen-aware + idempotent, clears delivery/shipping), `GetOrderSummaryUseCase` (backend amounts + real `missing_requirements`: `empty_order`, `delivery_type`, `delivery_address`, `payment_type`, `client`, `minimum_order_not_reached`), `GetCurrentOrderUseCase` (pure read: DRAFT > PENDING > latest, with readiness metadata), `GetLatestActiveOrderUseCase` (business + client/conversation scope, active states only) and `GetOrCreateCurrentDraftUseCase` (reuses `StartDraftOrderUseCase`). `ConfirmOrderUseCase` is now idempotent on retry (returns the confirmed state; a cancelled order still fails).
- [x] 3.5 RED: `OrderFilter` tests — `conversation_id`, `business_config_id`, `client_id`, `status_in`, `exclude_status_in`.
- [x] 3.6 GREEN: extended `OrderFilter` + Prisma repository filters.
- [x] 3.7/3.8 REST: `GET/POST /api/orders/draft/current/` (pure read vs idempotent get-or-create), `GET /api/orders/latest-active/`, `PATCH /api/orders/{id}/pickup/`, `GET /api/orders/{id}/summary/`. Verified end-to-end against the running backend (create/reuse draft, read readiness, summary missing requirements, pickup bumping the version, latest-active excluding drafts).
- [ ] 3.9 Verify: order REST + use-case suites green.

## Phase 4: Catalog Search

- [x] 4.1 RED: `ListProductsQuery.search` tests (`api/modules/catalog/tests/use_cases/test_list_products_search.py`) — the term is passed through and combines with `category_id` + `available`.
- [x] 4.2 GREEN: extended `ListProductsQuery`, `ListProductsUseCase` and the Prisma product repository (case-insensitive `contains` on name/description); exposed `?search=` in `GET /api/catalog/products/`. Verified end-to-end (`classic` -> 2, `burger` -> 8).
- [x] 4.3 Verify: catalog suites green.

## Phase 5: Conversation Application

- [x] 5.1 RED: `AgentExecutionContext` tests — required ids cannot be overridden by tool input.
- [x] 5.2 GREEN: added `AgentExecutionContext` + driven ports with conversation-owned DTOs: `CatalogServicePort`, `OrderServicePort` (reads, draft resolution and the reopen-aware/idempotent mutations, including checkout) and `DeliveryServicePort`.
- [x] 5.3 RED: `ResolveConversationForChannelUseCase` tests — same `(business, channel, externalThreadId)` resolves the same `Conversation`; different thread/business maps to a different conversation; the internal id is a RapidOS UUID, not the thread id.
- [x] 5.4 GREEN: implemented thread -> conversation resolution; `ConversationRepositoryPort.find_by_thread` + the Prisma repository now use the real `businessConfigId`/`externalThreadId` columns.
- [x] 5.5 RED: tested with fakes — informational catalog questions do not create an order; `quote_delivery` works with no order (no order read/created); the first `add_item` creates the draft and the second reuses it; a closed order raises `NEW_ORDER_REQUIRED` without creating anything; update/remove use `line_id`; a write without `externalMessageId` is rejected; the business/conversation always come from the context.
- [x] 5.6 GREEN: implemented the agent use cases (`catalog_queries`, `order_reads`, `order_mutations`, `delivery`) orchestrating only through the driven ports. `set_delivery` delegates to the order module (which quotes and only stores a delivery when available) so shipping is never computed in conversation.
- [ ] 5.7 RED: message-persistence flow tests — USER persisted, then ASSISTANT; agent failure still persists the USER message; `externalMessageId` stable across retry. (Needs the agent runner port; done with Phase 7.)
- [ ] 5.8 GREEN: implement `HandleIncomingMessageUseCase` (resolve context -> persist USER -> agent -> persist ASSISTANT). (With Phase 7.)
- [x] 5.9 Verify: conversation application suites green (fakes only, no DB): full suite 421 passed; import-linter 10/10.

## Phase 6: Conversation Infrastructure + Wiring

- [x] 6.1 RED: adapter tests with duck-typed stubs (`tests/infrastructure/test_cross_module_adapters.py`) — `CatalogServiceAdapter` / `OrderServiceAdapter` / `DeliveryServiceAdapter` delegate to the sibling driver ports and map DTOs; the post-commit cancellation is attempted for superseded attempts and a failing cancellation is swallowed.
- [x] 6.2 GREEN: implemented `conversation/infrastructure/adapters/driven/{catalog_service_adapter,order_service_adapter,delivery_service_adapter}.py`. `DeliveryServiceAdapter` reuses `CalculateDeliveryQuotePort`. Catches a real violation: the catalog adapter imported the catalog **domain** model; now it only uses the public port + the string state.
- [x] 6.3 GREEN: `build_container` now takes the cross-module services (and optional repositories for tests) and no longer builds in-memory repositories; conversation Prisma repositories resolve their client lazily (no I/O at import); `api/composition/container.py` wires the three adapters into the conversation container; the REST views resolve the container lazily.
- [x] 6.4 Verify: `uv run pytest` 431 passed; import-linter 10/10. Full chain verified against the real DB: resolve thread -> Conversation, catalog search/detail via the adapter, `add_item` created the draft + line, summary/missing requirements and the current-order read all worked.

## Phase 7: LangChain Driver + LangGraph/LangSmith

- [x] 7.1 RED: tool tests (`tests/infrastructure/test_langchain_tools.py`) — the exact 15-tool set, no administrative tools, identity cannot be overridden by a tool argument, argument→command mapping, no price/total/discount/shipping inputs, `set_payment_type` only CASH|ONLINE, business errors → structured code, technical errors → generic message without leaking details.
- [x] 7.2 GREEN: implemented the 15 thin tools (`langchain/tools.py`) bound to the trusted context, the versioned system prompt (`langchain/prompt.py`, `PROMPT_VERSION`) and the message flow (`HandleIncomingMessageUseCase` + `AgentRunnerPort`).
- [x] 7.3 RED: `LangChainConversationAgentAdapter` tests (`tests/infrastructure/test_langchain_agent_adapter.py`) — history → messages, final AI text extraction, tools built per context, the prompt policy is used; plus the message-persistence flow (USER before the agent, agent failure keeps the USER message, history excludes the new message).
- [x] 7.4 GREEN: `langchain_conversation_agent_adapter.py` (LangGraph `create_react_agent` + injectable model), `build_groq_model`, the separate Studio entrypoint `studio_graph.py` and `langgraph.json`; `langgraph-cli[inmem]` added as a dev dependency; run instructions in the adapter README. Tracing is env-driven (no secrets in metadata).
- [x] 7.5 Verify: tool/agent/studio suites green (full suite 449 passed; import-linter 10/10). The graph compiles with no warnings and no I/O at import. `POST /api/conversation/agent/message/` added as a driver entrypoint (503 without a Groq key); documented how to run from Studio.

## Phase 8: Tests, Gates, Docs, Report

- [x] 8.1 Agent-policy scenarios: deterministic prompt-policy tests (`tests/infrastructure/test_agent_policy.py`) plus the 8 LLM-behaviour scenarios as a LangSmith eval dataset (`langchain/evals/agent_policy_scenarios.json`).
- [x] 8.2 Updated `docs/order-state-machine.md` (ONLINE/CASH graphs, reopen, cancellation set) and reconciled `docs/reglas-negocio.md` (RN-006b reopen, RN-008b manual orders, RN-014 `PAGADO -> CONFIRMADO -> EN_PREPARACION`).
- [x] 8.3 Gates: `uv run pytest` 464 passed; import-linter 10/10; `manage.py check` clean; `prisma validate` valid.
- [x] 8.4 `apply-progress.md` + the final report with the explicit confirmation checklist.
- [~] 8.5 `state.yaml` updated to `verification_status: pass` (archive pending).
