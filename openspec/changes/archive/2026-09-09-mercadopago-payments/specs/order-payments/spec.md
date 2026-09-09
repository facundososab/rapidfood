# Order Payments Specification

## Purpose

Order-owned online payment attempts for Mercado Pago Checkout links and webhook-driven order payment state.

## Requirements

### Requirement: Payment link creation

The system MUST create a Mercado Pago payment link only for an existing `ONLINE` order in `PENDING` with a positive total, create a local `Payment(PENDING)`, persist provider identifiers/link, and return plain response data.

#### Scenario: Create link for payable order
- GIVEN an order exists with status `PENDING`, payment type `ONLINE`, and total > 0
- WHEN payment link creation is requested
- THEN a `PENDING` payment is associated to the order
- AND the response includes `order_id`, `payment_id`, `provider`, `checkout_url`, and `PENDING`

#### Scenario: Reject invalid link creation
- GIVEN the order is missing, not `PENDING`, not `ONLINE`, or has no positive total
- WHEN payment link creation is requested
- THEN no provider link is created and no payment attempt is persisted
- AND the caller receives a validation/not-found error that does not expose provider details

### Requirement: Provider-authoritative notification processing

The system MUST handle Mercado Pago notifications by fetching authoritative remote payment state before mutating local `Payment` or `Order`; raw webhook payload status MUST NOT be trusted.

#### Scenario: Authoritative lookup precedes mutation
- GIVEN a notification references a Mercado Pago payment/preference
- WHEN the notification is processed
- THEN the provider is queried for the remote payment
- AND local state changes use the fetched remote state only

#### Scenario: Duplicate notification is idempotent
- GIVEN a notification for a payment already processed with the same final state
- WHEN the notification is received again
- THEN no duplicate payment is created and no order transition is repeated
- AND the webhook response remains successful

### Requirement: Payment status mapping and order transition

The system MUST map provider statuses to `APPROVED`, `REJECTED`, `FAILED`, or `EXPIRED`. `APPROVED` MUST move an order from `PENDING` to `PAID`; `REJECTED`, `FAILED`, and `EXPIRED` MUST keep the order `PENDING`.

#### Scenario: Approved payment pays order
- GIVEN a local payment belongs to a `PENDING` order
- WHEN the authoritative provider state maps to `APPROVED`
- THEN the payment becomes `APPROVED`
- AND the order becomes `PAID`

#### Scenario: Non-approved payment keeps order pending
- GIVEN a local payment belongs to a `PENDING` order
- WHEN the authoritative provider state maps to `REJECTED`, `FAILED`, or `EXPIRED`
- THEN the payment stores that mapped state
- AND the order remains `PENDING`

### Requirement: REST and conversation boundaries

The system MUST expose REST driver endpoints for link creation and Mercado Pago notifications, with HTTP adapters only translating protocol data to use-case commands. Conversation delivery MUST remain deferred until the order flow is stable, but retry copy expectations MUST be preserved.

#### Scenario: REST endpoints delegate to use cases
- GIVEN `POST /api/orders/{order_id}/payment-link/` or `POST /api/orders/payments/mercadopago/webhook/`
- WHEN a valid request reaches the endpoint
- THEN the view delegates to the corresponding payment use case
- AND business rules stay out of serializers/views

#### Scenario: Deferred conversation messaging
- GIVEN conversation integration is later wired through a port
- WHEN a link is created, approved, rejected, failed, or expired
- THEN messages can say pending-payment, payment-confirmed, or offer a new payment link retry

### Requirement: Hexagonal payment architecture

The system MUST keep Mercado Pago SDK/API, Django, DRF, and Prisma in infrastructure/adapters only. Domain/application MUST use ports and plain data, with explicit composition-root wiring and no globals/service locator.

#### Scenario: Dependency direction is enforced
- GIVEN payment domain/application code is inspected by import-linter
- WHEN `uv run lint-imports` runs in verification
- THEN no domain/application import depends on Django, DRF, Prisma, or Mercado Pago
