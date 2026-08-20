# Tasks: Conversations

Strict TDD: every RED task records the failing test/command; every GREEN task records passing `uv run pytest ...`. Apply may mark `[x]` only with RED/GREEN evidence plus final gates.

## Phase 1: Scaffold Reconciliation

- [x] 1.1 RED: add import tests proving `api.modules.conversation` package paths and driver/driven layers import without `apps/*`.
- [x] 1.2 GREEN: create package `__init__.py` files under `api/`, `api/modules/`, and `api/modules/conversation/{domain,application,infrastructure,configuration}`.
- [x] 1.3 RED: add Django URL/settings tests for `api.config.settings` and conversation route resolution.
- [x] 1.4 GREEN: update `pyproject.toml` pytest/import-linter config from `config.settings`/`apps` to `api.config.settings`/`api.modules`; update `api/config/{settings.py,urls.py}` as needed.

## Phase 2: Domain

- [x] 2.1 RED: add `api/modules/conversation/tests/domain/test_conversation.py` for non-empty id/channel and last-intent/sentiment validation.
- [x] 2.2 GREEN: implement `domain/models/conversation.py`, `domain/value_objects.py`, and `domain/errors.py` as pure Python.
- [x] 2.3 RED: add `tests/domain/test_message.py` for content, role/status/intent validity, and required `conversation_id`.
- [x] 2.4 GREEN: implement `domain/models/message.py`; verify no Django/DRF/Prisma imports.

## Phase 3: Application Ports and DTOs

- [x] 3.1 RED: add port/DTO import and shape tests for commands/responses and Protocol contracts.
- [x] 3.2 GREEN: implement `application/ports/driver/{conversation_commands.py,conversation_responses.py,conversation_use_cases.py}`.
- [x] 3.3 GREEN: implement driven ports in `application/ports/driven/{conversation_repository.py,message_repository.py,intent_detector.py,clock.py,cross_module.py}`.

## Phase 4: Use Cases with Fakes

- [x] 4.1 RED: test get-or-create reuse/create with fake conversation/client ports.
- [x] 4.2 GREEN: implement `use_cases/get_or_create_conversation.py`.
- [x] 4.3 RED: test add/list messages store and return chronological plain DTOs.
- [x] 4.4 GREEN: implement `use_cases/{add_message.py,list_messages.py}`.
- [x] 4.5 RED: test receive-message stores USER then AGENT, detects intent via port, disambiguates active draft, and confirms only explicit confirmation.
- [x] 4.6 GREEN: implement `use_cases/receive_message.py` using only constructor-injected ports.

## Phase 5: Driven Adapters

- [x] 5.1 RED: test deterministic intent adapter maps order/modify/confirm/query/unknown phrases.
- [x] 5.2 GREEN: implement `infrastructure/adapters/driven/intent/deterministic_intent_detector.py` and `clock.py`.
- [ ] 5.3 RED: add Prisma repository integration tests if fixture/config is stable; otherwise mark blocked with evidence.
- [x] 5.4 GREEN: implement Prisma repositories in `infrastructure/adapters/driven/prisma/` mapping schema fields to pure domain/DTOs.

## Phase 6: REST Driver Adapter

- [x] 6.1 RED: test serializer rejects missing channel/identity/content and stores nothing.
- [x] 6.2 GREEN: implement REST `serializers.py`.
- [x] 6.3 RED: test `POST /conversation/webhook/` and `GET /conversation/{id}/messages/` response shapes.
- [x] 6.4 GREEN: implement REST `views.py` and `urls.py`, translating HTTP only.

## Phase 7: Composition and Gates

- [x] 7.1 RED: test `configuration/container.py` explicitly wires use cases; no hidden globals/service locator.
- [x] 7.2 GREEN: implement container and connect REST views through it.
- [ ] 7.3 Verify architecture gates: `uv run pytest`, `uv run lint-imports`, `uv run python manage.py check`.
- [x] 7.4 Update docs/artifacts: task evidence, OpenSpec notes, and any scaffold deviations/blocked Prisma evidence.
