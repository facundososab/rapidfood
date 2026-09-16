# Delta for Scaffold

## MODIFIED Requirements

### Requirement: Hexagonal App Structure

Runtime modules MUST live under `api/modules/` for client, conversation, order, catalog, and config_coupon. Each module MUST preserve domain, application ports/use_cases, application ports/driven or driver contracts, infrastructure adapters/driven or driver adapters, and configuration/composition packages. Stale `apps/*` references MUST NOT guide this change.
(Previously: scaffold text described `apps/*` as the active package layout.)

#### Scenario: Modules import cleanly
- GIVEN the scaffold installed
- WHEN Django loads INSTALLED_APPS
- THEN the five `api/modules/*` bounded contexts import without error

### Requirement: Architecture Contracts

`[tool.importlinter]` MUST define contracts for `modules.*`: (1) layers per module (infrastructure/adapters → application → domain); (2) forbidden Django/DRF/Prisma/Mercado Pago imports from domain and application use cases; (3) forbidden cross-module imports except via application ports or explicit composition-root wiring. `uv run lint-imports` MUST pass.
(Previously: contracts referenced `apps.*` and only scaffold-time framework bans.)

#### Scenario: Framework ban enforced
- GIVEN a payment use case imports Prisma or Mercado Pago SDK
- WHEN `uv run lint-imports` runs
- THEN the forbidden contract fails, naming the import

#### Scenario: Port-only cross-module edge
- GIVEN conversation needs order payment-link behavior
- WHEN it imports an order application port or a composition-provided adapter
- THEN the edge is allowed without importing order infrastructure

#### Scenario: Payment provider isolation
- GIVEN Mercado Pago SDK is imported outside infrastructure
- WHEN `uv run lint-imports` runs
- THEN the architecture contract fails and identifies the forbidden import
