# Exploration: conversations

## Current State

- Branch is `conversations`.
- `docs/` is the authoritative source for this change. Notion must remain secondary and must not override the docs.
- The docs define the conversation context as the AI/conversational module that records conversations/messages and orchestrates draft-order building through ports, not by directly mutating other bounded contexts.
- The Prisma schema already contains `Conversation`, `Message`, and `Order.conversationId`, matching the docs' core relationships.
- There is a major scaffold inconsistency before implementation: project guidance and OpenSpec scaffold artifacts disagree with the current worktree. `docs/ARCHITECTURE-GUIDE.md` and `AGENTS.md` point to `api/modules/*` with `application/ports/{driver,driven}` and `infrastructure/adapters/{driver,driven}`, while `pyproject.toml`, README, import-linter contracts, and prior scaffold specs point to root `apps/*` with `application/ports/{inbound,outbound}`, `adapters/{inbound,outbound}`, and root `config`. The actual worktree currently has `api/modules/*` skeleton directories with only `.gitkeep`, root `apps/*` directories containing only `__pycache__`/migrations artifacts, and no tracked source packages under `apps/*`.
- Current git status before this exploration: branch `conversations`; modified `.atl/skill-registry.md` and `.gitignore` pre-existed. This phase adds only this exploration artifact.

## Docs Requirements for Conversation

### Entities and relationships

- `conversation`: `conversationId`, `overallSentiment`, `lastIntent`, `channel`.
- `message`: `messageId`, `role`, `content`, `detectedIntent`, `sentiment`, `status`.
- Relationships from `docs/modelo-dominio.md` and schema:
  - `client 1..* -- 0..* conversation` (schema currently `Conversation.clientId` nullable).
  - `conversation 1..1 -- 1..* message` (`Message.conversationId` required).
  - `conversation` indirectly owns draft-building context through `order.conversationId` (RN-030/RN-031); one conversation can have many orders but only one active `BORRADOR` order.

### Functional requirements

- REQ-015/027: create a `BORRADOR` order when the agent detects intent to start an order.
- REQ-028/029/052/053: detect an existing non-expired draft for the conversation and ask whether to continue or start over.
- REQ-030/031: build/update the draft as the customer mentions or changes products.
- REQ-032/038/040/041: report current draft status, specific order status, and recent client orders.
- REQ-033: ask for missing delivery type, address for `ENVIO`, and payment method before confirmation.
- REQ-034: validate product availability, coverage zone, and business hours in real time before confirmation.
- REQ-035/036/037: show updated totals, require explicit confirmation before `PENDIENTE`, and report estimated time after confirmation.
- REQ-045/051: later increments need customer notifications on order-state changes and payment retry guidance.

### Business rules and state machine implications

- RN-001/RN-028/RN-030: conversation starts or resumes exactly one active `BORRADOR` order per conversation.
- RN-002/RN-006/RN-020..023: draft orders are freely mutable and incomplete; full validation only happens on `BORRADOR -> PENDIENTE`.
- RN-003/RN-008/RN-023/RN-024/RN-025: explicit customer confirmation triggers `BORRADOR -> PENDIENTE`, validates all required data, freezes line prices, and calculates estimated time.
- RN-005/REQ-025: inactive drafts expire/clean after 24 hours; first increment should at least model/read this invariant, even if scheduled cleanup is deferred.
- RN-029: if a customer requests a new order while a draft exists, the agent must ask a disambiguation question rather than silently abandoning or reusing the draft.
- RN-031: confirmed or later orders remain associated with the conversation history.
- `order-state-machine.md` makes the conversation module a state-machine driver for draft creation/confirmation only; operational transitions after `PENDIENTE` belong to order/payment/business workflows, with conversation only notifying or reporting via ports.

## Affected Areas

- `docs/modelo-dominio.md` — source of entities, fields, and relationships for conversation/message/order/client.
- `docs/req-funcionales.md` — source of REQ-015 and REQ-027..053 behavior.
- `docs/reglas-negocio.md` — source of RN-001..031 conversation/order invariants and draft constraints.
- `docs/order-state-machine.md` — source of allowed order transitions conversation must respect.
- `docs/ARCHITECTURE-GUIDE.md` and `AGENTS.md` — say modules live under `api/modules/` and use driver/driven terminology.
- `pyproject.toml` and `README.md` — currently configure/import-lint root `apps/*`, root `config`, and inbound/outbound terminology.
- `api/shared/infrastructure/prisma/schema.prisma` — existing data model for `Conversation`, `Message`, and `Order.conversationId`.
- `api/modules/conversation/` — docs-aligned module skeleton, but currently only `.gitkeep` placeholders.
- `apps/conversation/` — import-linter/README-aligned location, but currently lacks source files and packages in the worktree.
- `api/config/urls.py` / `api/config/settings.py` and root `manage.py` — REST exposure/wiring is blocked by config path mismatch (`config.settings` at root vs actual `api/config/settings.py`).
- `openspec/specs/scaffold/spec.md` and `openspec/changes/scaffold-inicial/*` — prior artifacts document expected scaffold and known drift; they must be reconciled with the actual worktree before coding.

## Dependencies Conversation Must Use Via Ports Only

- `client`: identify or create/find client by channel identity (phone number), list confirmed/recent orders by client if exposed from order through ports; conversation must not import client adapters or storage.
- `order`: required `OrderDraftPort`-style inbound contract for `create_draft`, `get_draft_by_conversation`, `add_line`, `remove_line`, `set_quantity`, `apply_coupon`, `remove_coupon`, `confirm`, and `abandon`; conversation must never mutate order tables directly.
- `catalog`: product search/lookup and current availability/price through product query ports before adding/updating draft lines.
- `config_coupon`: business configuration/hours/coverage checks and coupon validation/application through ports when needed.
- Additional conversation-owned outbound ports: conversation/message repository, clock (24h draft expiry and timestamps), intent detector, optional sentiment analyzer, optional notifier/channel gateway, and logger. These are capabilities, not technologies.

## Approaches

1. **Deterministic first increment (recommended)** — Implement a rules/keyword intent detector behind an `IntentDetectorPort`, webhook inbound adapter, conversation/message persistence, and draft-order orchestration through ports.
   - Pros: deterministic tests, no external LLM dependency, respects docs, enables strict TDD, and proves architecture boundaries early.
   - Cons: limited natural-language quality; product parsing will be basic and may need later replacement.
   - Effort: Medium.

2. **LLM adapter first** — Implement an outbound LLM gateway behind the same intent/analyzer ports and use it for intent/product extraction from the start.
   - Pros: better natural-language coverage sooner.
   - Cons: non-deterministic, secrets/config required, harder tests, higher risk of violating docs-driven behavior if prompts become the source of truth.
   - Effort: High.

3. **Scaffold reconciliation first** — Before any conversation business implementation, align the repository around exactly one module layout and package path (`api/modules` vs `apps`, `driver/driven` vs `inbound/outbound`, `api/config` vs root `config`).
   - Pros: removes the biggest blocker and prevents building on a broken import-linter/test target.
   - Cons: delays user-visible conversation behavior.
   - Effort: Medium, but likely mandatory.

## Recommendation

Proceed in two steps:

1. **Resolve scaffold/layout consistency before implementation.** Pick one canonical layout. Because the hard instruction says implementation must be guided absolutely by `./docs`, the docs currently favor `api/modules/*`, `api/config`, and `driver/driven`; however, existing import-linter/OpenSpec scaffold favors root `apps/*`, root `config`, and `inbound/outbound`. Do not silently mix both.
2. **For the first conversation increment, use deterministic intent detection behind ports, not a direct LLM dependency.** Scope it to: inbound webhook, message persistence/listing, conversation upsert by channel identity, active draft lookup/creation, basic intent/result response, and use-case unit tests with fake ports. Keep LLM as a later adapter that can implement the same port.

Suggested first increment boundaries:

- Bounded context: `conversation`.
- Aggregate/entities: `Conversation`, `Message`; order draft remains owned by `order`.
- Primary use case: `ReceiveConversationMessageUseCase` (or equivalent) receives plain input, stores inbound message, detects intent, calls order/catalog/client/config ports as needed, stores agent response, returns plain response DTO.
- REST exposure: one webhook endpoint and one message-list endpoint, after layout is reconciled.
- Persistence: conversation/message repository adapter via Prisma, hidden behind a conversation outbound port.
- Tests: unit tests for use-case orchestration with fake ports; adapter integration tests only after scaffold/package path is stable.

## Risks

- **Blocker: scaffold/layout drift.** Actual files do not match either fully documented layout. `api/modules/*` exists as `.gitkeep` skeletons; root `apps/*` lacks source packages; import-linter targets `apps`; Django settings point to `apps.*`; root `manage.py` points to `config.settings` while actual settings are under `api/config`.
- **Pre-existing working tree changes.** `.atl/skill-registry.md` and `.gitignore` are modified and should not be overwritten by implementation agents.
- **Port terminology drift.** User/project standards say inbound/outbound; docs skill says driver/driven; scaffold artifacts have both and specifically flag `OrderDraftPort` path drift.
- **Domain ownership risk.** Conversation should orchestrate but not own order business rules; confirmation, totals, price freezing, and state transitions belong to `order` use cases exposed as ports.
- **LLM nondeterminism risk.** Starting with an LLM adapter makes strict TDD and docs compliance harder; defer until deterministic contract is proven.
- **Draft expiry needs a clock port.** Without a clock port, 24h rules will become hard to test.
- **Product parsing ambiguity.** The docs require building orders from mentioned products, but do not define parsing grammar; first increment should document a narrow deterministic grammar or defer free-text extraction.

## Manual Verification for This Phase

No tests are expected for exploration. Manually inspect:

- `openspec/changes/conversations/exploration.md` — this artifact.
- `docs/modelo-dominio.md` lines 35-49 and 122-123 — conversation/message fields and relationships.
- `docs/req-funcionales.md` lines 20-75 — order draft, agent, query, transitions, payments, recovery requirements.
- `docs/reglas-negocio.md` lines 3-41 — draft and conversation/order invariants.
- `docs/order-state-machine.md` — allowed order transitions.
- `docs/ARCHITECTURE-GUIDE.md` lines 20-58 — docs-level module/layer layout.
- `pyproject.toml` lines 38-131 and README lines 47-67 — current root `apps/*` import-linter/readme assumptions.
- `api/shared/infrastructure/prisma/schema.prisma` lines 108-134 and 136-158 — current conversation/message/order schema.
- `git status --short --branch` — confirms branch and pre-existing modified files plus this artifact.

## Ready for Proposal

Yes, but the orchestrator should ask the user to choose/confirm the canonical scaffold layout before design/apply. Recommended next phase is `sdd-propose` only if it explicitly includes scaffold reconciliation as a prerequisite/blocker; otherwise run a dedicated scaffold-fix change first.
