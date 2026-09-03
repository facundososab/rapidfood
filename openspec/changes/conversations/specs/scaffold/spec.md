# Delta for Scaffold

## ADDED Requirements

### Requirement: Canonical Conversation Scaffold Reconciliation

For the `conversations` change, the implementation scaffold MUST follow `docs/ARCHITECTURE-GUIDE.md` and `AGENTS.md` as canonical guidance, not README. The conversation module MUST live under `api/modules/conversation/` with `domain/`, `application/use_cases/`, `application/ports/driver/`, `application/ports/driven/`, `infrastructure/adapters/driver/`, `infrastructure/adapters/driven/`, and `configuration/`. Django URL/settings wiring and import paths MUST be reconciled enough for tests and runtime checks to import this canonical module without relying on hidden globals or a service locator.

#### Scenario: Canonical package imports

- GIVEN the repository is installed for tests
- WHEN `api.modules.conversation` and its layer packages are imported
- THEN imports resolve from `api/modules/conversation`
- AND no implementation path depends on root `apps/conversation`

#### Scenario: Explicit composition root

- GIVEN the webhook driver adapter needs a receive-message use case
- WHEN dependencies are assembled
- THEN assembly happens in `api/modules/conversation/configuration/`
- AND adapters or use cases do not construct hidden global dependencies

#### Scenario: URLs expose conversation endpoints

- GIVEN Django loads project URLs
- WHEN conversation webhook and message-list routes are resolved
- THEN they point to driver adapters under `api/modules/conversation/infrastructure/adapters/driver/`

### Requirement: Canonical Layer and Port Terminology

Architecture contracts for this change MUST allow inward dependencies only: infrastructure/adapters → application → domain. Application ports MUST use `driver` and `driven` terminology for canonical docs alignment. Domain MUST NOT import framework, ORM, web, adapter, or cross-module types. Cross-module communication MUST be port-only.

#### Scenario: Domain remains pure

- GIVEN a domain file imports Django, DRF, Prisma, or another module adapter
- WHEN architecture checks run
- THEN the violation is detected

#### Scenario: Cross-module edge is port-only

- GIVEN conversation needs order draft behavior
- WHEN it imports the order capability
- THEN it imports an application port/protocol only
- AND never imports order storage, repository implementation, adapter, or model code

### Requirement: Scaffold Verification for Strict TDD

Before implementing business code, the scaffold MUST support writing failing tests against the canonical package paths. Test configuration SHOULD keep strict TDD enabled and SHOULD be compatible with `uv run pytest`, `uv run lint-imports`, and `uv run python manage.py check` once code exists.

#### Scenario: Failing test can target canonical path

- GIVEN no conversation behavior is implemented yet
- WHEN a test imports the planned use-case or port path
- THEN the failure is about missing behavior or symbol
- AND not about ambiguous `apps/*` versus `api/modules/*` layout
