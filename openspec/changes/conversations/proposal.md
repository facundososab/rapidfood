# Proposal: Conversations

## Intent

Implement the `conversation` module from the project docs: persist conversations/messages, receive webhook messages, detect intent deterministically, and orchestrate draft-order behavior through ports. This change intentionally follows `docs/ARCHITECTURE-GUIDE.md`, `AGENTS.md`, and domain docs; README `apps/*` guidance is ignored until docs/repo scaffold are reconciled.

## Scope

### In Scope
- Domain: `Conversation`, `Message`, message roles/status/intent/sentiment value objects as plain Python.
- Use cases: `GetOrCreateConversation`, `AddMessage`, `ListMessages`, `ReceiveConversationMessage`/`HandleIncomingMessage`.
- Deterministic intent detector behind a driven port; no direct LLM dependency.
- Driver adapters: REST webhook receive endpoint and message-list endpoint.
- Driven adapters: Prisma conversation/message repository if package/config layout is reconciled enough to wire safely.
- Canonical layout: `api/modules/conversation/{domain,application,infrastructure,configuration}`, `application/ports/{driver,driven}`, `infrastructure/adapters/{driver,driven}`.

### Out of Scope
- Full LLM integration, advanced product extraction NLP, payment provider integration, business admin UI/API.
- Implementing the full order state machine outside conversation; conversation may only drive draft creation/update/confirmation through order ports.

## Capabilities

### New Capabilities
- `conversations`: Conversation/message persistence, webhook orchestration, intent detection contract, and listing messages.

### Modified Capabilities
- `scaffold`: Reconcile or override current `apps/*`/inbound-outbound assumptions for this change with docs-canonical `api/modules/*` and driver/driven layout.

## Approach

Use hexagonal boundaries strictly. Driver adapters convert HTTP/webhook payloads to commands; use cases orchestrate plain DTOs and domain objects; driven adapters implement ports. Dependencies are constructor-injected via explicit `configuration/` composition root; no hidden globals/service locator.

## Affected Areas

| Area | Impact | Description |
|---|---|---|
| `api/modules/conversation/` | New | Domain, use cases, ports, adapters, composition |
| `api/config/urls.py` / settings | Modified | REST route wiring if layout is reconciled |
| `api/shared/infrastructure/prisma/schema.prisma` | Referenced | Existing Conversation/Message schema source |
| `openspec/specs/scaffold/spec.md` | Modified | Current spec conflicts with canonical docs layout |

## Dependencies

- Defines conversation-owned driven ports: `ConversationRepositoryPort`, `MessageRepositoryPort`, `IntentDetectorPort`, `ClockPort`.
- Consumes other modules only through ports: client identity lookup/create, order draft operations, catalog product lookup/availability, config/coupon business rules where needed.

## Risks

| Risk | Likelihood | Mitigation |
|---|---|---|
| Repo/spec layout mismatch (`apps/*` vs `api/modules/*`) | High | Treat docs/AGENTS as canonical for this change; capture scaffold delta before apply |
| Import-linter/settings still target old layout | High | Reconcile contracts/config before or during first implementation increment |
| Conversation oversteps order ownership | Med | Call order ports only; no direct order persistence |
| Deterministic detector is limited | Med | Keep it swappable behind a port |

## Rollback Plan

Remove new conversation module files, URL wiring, and any scaffold delta/spec additions. If Prisma adapter changes land, revert only repository wiring/adapters; schema already contains conversation/message models.

## Success Criteria

- [ ] Specs/design can target docs-canonical `api/modules/*` without README ambiguity.
- [ ] Webhook persists inbound and agent messages and returns a plain response DTO.
- [ ] List messages returns persisted conversation history.
- [ ] Use-case tests use fake ports; adapters are integration-tested when config allows.
- [ ] Later verification commands expected, not run now: `uv run pytest`, `uv run lint-imports`, `uv run python manage.py check`.
