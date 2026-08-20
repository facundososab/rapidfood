# Design: Conversations

## Technical Approach

Implement `conversation` as a docs-canonical hexagonal module under `api/modules/conversation/`. Django/DRF remains only the HTTP shell; use cases receive plain commands, call domain objects and ports, and return DTOs. Prisma is used only by driven adapters. README `apps/*` guidance is ignored for this change; scaffold config must be reconciled to import `api.*` packages.

## Architecture Decisions

| Decision | Choice | Alternatives / tradeoff | Rationale |
|---|---|---|---|
| Module layout | `api/modules/conversation/{domain,application,infrastructure,configuration}` | Root `apps/*` matches current `pyproject`, but conflicts with canonical docs | User mandate and docs/AGENTS are authoritative |
| Intent detection | Deterministic keyword/rule adapter behind `IntentDetectorPort` | LLM first gives broader NLP but needs secrets and non-deterministic tests | Strict TDD and replaceability |
| Persistence | Prisma repository adapter maps existing `Conversation`/`Message` models | Django ORM adapter would violate Prisma-as-source | Schema already has required tables |
| Cross-module work | Consume application ports only | Direct order/catalog/client storage is faster but breaks boundaries | Conversation orchestrates; order owns order invariants |

## Data Flow

```text
HTTP webhook -> REST adapter -> ReceiveMessageUseCase
  -> GetOrCreateConversation -> repositories/client port
  -> MessageRepository.save(USER)
  -> IntentDetectorPort.detect
  -> optional catalog/order/config ports
  -> MessageRepository.save(AGENT)
  -> Response DTO -> HTTP JSON
```

## File Changes

Create exact tree:

```text
api/modules/conversation/
  __init__.py
  domain/{__init__.py,models/conversation.py,models/message.py,value_objects.py,errors.py}
  application/{__init__.py,use_cases/{__init__.py,get_or_create_conversation.py,add_message.py,list_messages.py,receive_message.py},ports/driver/{__init__.py,conversation_commands.py,conversation_responses.py,conversation_use_cases.py},ports/driven/{__init__.py,conversation_repository.py,message_repository.py,intent_detector.py,clock.py,cross_module.py}}
  infrastructure/{__init__.py,adapters/driver/rest/{__init__.py,serializers.py,views.py,urls.py},adapters/driven/prisma/{__init__.py,conversation_repository.py,message_repository.py},adapters/driven/intent/{__init__.py,deterministic_intent_detector.py},adapters/driven/clock.py}
  configuration/{__init__.py,container.py}
  tests/{domain/test_conversation.py,test_message.py,use_cases/test_get_or_create_conversation.py,test_add_message.py,test_list_messages.py,test_receive_message.py,integration/test_conversation_repository_prisma.py,test_conversation_rest.py}
```

Modify: `api/config/urls.py` include `conversation/`; `api/config/settings.py` install docs-canonical app paths or omit module apps if no Django AppConfig; `pyproject.toml` import-linter/pytest paths from `apps`/`config.settings` to `api.modules`/`api.config.settings`; add package `__init__.py` files under `api/`, `api/modules/`, shared paths as needed. No schema migration expected: Prisma already has `Conversation`/`Message` and `Order.conversationId`.

## Interfaces / Contracts

Domain: `Conversation(id, channel, client_id?, overall_sentiment?, last_intent?)`; `Message(id, conversation_id, role, content, detected_intent?, sentiment?, status, created_at?)`. Enums/value objects: `MessageRole(USER, AGENT, SYSTEM)`, `MessageStatus(RECEIVED, PROCESSED, FAILED)`, `DetectedIntent(START_ORDER, MODIFY_ORDER, CONFIRM_ORDER, QUERY_DRAFT, QUERY_ORDER, UNKNOWN)`, `Sentiment(positive, neutral, negative)`, `Channel` non-empty. Invariants: non-empty ids/channel/content; message belongs to exactly one conversation; role/status/intent values must be valid; confirmation intent is not enough to mutate order without explicit confirmation text.

Driver ports expose commands/responses for `GetOrCreateConversation`, `AddMessage`, `ListMessages`, `ReceiveMessage`: channel identity, content, role, pagination/order fields; responses are plain dataclasses/dicts, never DRF/Prisma types.

Driven ports: `ConversationRepositoryPort(find_by_channel_identity, create, save_last_intent)`, `MessageRepositoryPort(add, list_by_conversation)`, `IntentDetectorPort(detect)`, `ClockPort(now)`, plus cross-module protocols for client identity, order draft lookup/create/update/confirm/abandon, catalog product lookup, business config/coupon validation. Cross-module imports must target application port protocols only.

REST adapter shape: `POST /conversation/webhook/` body `{channel, channel_identity, content, external_message_id?}` returns `{conversation_id, user_message_id, agent_message_id, intent, response}`. `GET /conversation/{conversation_id}/messages/` returns `{conversation_id, messages:[...]}` chronological.

## Testing Strategy

| Layer | RED/GREEN sequence |
|---|---|
| Domain | First fail on empty content/invalid role/no conversation id, then implement value objects/entities |
| Use cases | Fake all driven ports; prove upsert reuse/create, chronological list, receive stores user then agent and calls order ports only when needed |
| Adapters | Serializer invalid payload stores nothing; URL resolves; Prisma mapper round-trips existing schema fields |
| Architecture | Update import-linter contracts, then add violation-focused tests/check expectations |

## Migration / Rollout

No DB migration required. Roll out scaffold reconciliation first, then domain/use-case tests, then adapters/composition.

## Open Questions

- [ ] Exact product parsing grammar for deterministic detector remains intentionally narrow for first increment.
- [ ] Whether current `api/shared/infrastructure/prisma/db.py` singleton should be replaced with request-scoped lifecycle later; keep constructor injection now.
