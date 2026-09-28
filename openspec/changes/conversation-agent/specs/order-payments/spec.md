# Order Payments Specification (delta)

## Purpose

Rework order-owned online payments to Mercado Pago **Checkout Pro + Orders API** with versioned payment attempts, provider idempotency keys, and webhook validation that prevents a stale checkout from paying the current order version.

## MODIFIED Requirements

### Requirement: Payment link creation

The system MUST create a Mercado Pago checkout only for an existing `ONLINE` order in `PENDING` with a positive total, MUST reserve exactly one logical `PaymentAttempt` for the order's current `version` before the remote call, MUST persist a stable provider idempotency key for the creation, and MUST reuse that key on retry. The system MUST use the Mercado Pago **Orders API** (`POST /v1/orders`) with an `X-Idempotency-Key` header. `run_id` MUST NOT be used as the provider key.

#### Scenario: Checkout for a payable order
- GIVEN an order exists with status `PENDING`, payment type `ONLINE` and total > 0
- WHEN checkout creation is requested
- THEN a single logical `PaymentAttempt` MUST be reserved for the current `version`
- AND a provider idempotency key for creation MUST be persisted
- AND the Orders API MUST be called with that key
- AND the response MUST expose the checkout identity and URL

#### Scenario: Reject invalid checkout creation
- GIVEN the order is missing, not `PENDING`, not `ONLINE`, or has no positive total
- WHEN checkout creation is requested
- THEN no provider checkout MUST be created
- AND no `PaymentAttempt` MUST be persisted

#### Scenario: Create timeout retry reuses the provider key
- GIVEN a checkout creation that timed out after a local `PaymentAttempt` was reserved
- WHEN creation is retried for the same logical attempt
- THEN the same provider idempotency key MUST be reused
- AND no additional logical checkout MUST be created

#### Scenario: Only one current attempt per version
- GIVEN an order `version = N` with a current attempt
- WHEN checkout creation is retried
- THEN no additional logical attempt MUST be created for that version

#### Scenario: Checkout rejected after reopen
- GIVEN an order was reopened to `DRAFT`
- WHEN checkout creation is requested before a new confirmation
- THEN it MUST be rejected

### Requirement: Payment attempt semantics

Each attempt MUST record the `orderVersion` it was created for, its amount, its provider status and its local validity (`supersededAt`) as **separate** concepts, so an attempt can be simultaneously approved by the provider and superseded locally.

#### Scenario: Approved and superseded coexist
- GIVEN an attempt for an older version that the provider later approved
- WHEN the attempt is persisted
- THEN `providerStatus = APPROVED` and `supersededAt` MUST be set

#### Scenario: Supersede on modification
- GIVEN a current attempt for `version = N`
- WHEN the order is modified to `version = N + 1`
- THEN the previous attempt MUST be marked superseded
- AND its amount and `orderVersion` MUST NOT be updated

### Requirement: Provider-authoritative notification processing

The system MUST handle Mercado Pago notifications by fetching authoritative remote state before mutating local state, MUST locate the `PaymentAttempt` by the provider external identifier (unique per provider), and MUST NOT trust the raw webhook payload status.

#### Scenario: Authoritative lookup precedes mutation
- GIVEN a notification references a provider checkout/payment
- WHEN the notification is processed
- THEN the provider MUST be queried for the remote state
- AND local state changes MUST use the fetched state only

#### Scenario: Attempt resolved by external identity
- GIVEN multiple attempts for the same order
- WHEN a notification arrives for one provider external identifier
- THEN the matching attempt MUST be resolved by that identifier
- AND the lookup MUST NOT assume "the current attempt"

#### Scenario: Duplicate notification is idempotent
- GIVEN a notification for an attempt already processed with the same final state
- WHEN it is received again
- THEN no duplicate attempt MUST be created and no order transition MUST be repeated

### Requirement: Webhook payment validation

Before applying any order transition on an `APPROVED` notification, the system MUST verify that `paymentAttempt.orderId == order.id`, `paymentAttempt.orderVersion == order.version`, `paymentAttempt.amount` equals the expected current amount, and the attempt is not superseded.

#### Scenario: Current version with correct amount pays the order
- GIVEN an `APPROVED` notification for the current version, matching order, matching amount and a non-superseded attempt
- WHEN the notification is processed
- THEN the order MUST transition to `PAID`

#### Scenario: Stale approved attempt does not pay
- GIVEN an attempt for `orderVersion = 5` while the order is at `version = 6`
- WHEN the provider reports `APPROVED`
- THEN `providerStatus = APPROVED` MUST be persisted
- AND the order MUST NOT become `PAID` or `CONFIRMED`
- AND the attempt MUST remain available for refund/reconciliation

#### Scenario: Wrong amount does not pay
- GIVEN an `APPROVED` notification for the current version with a mismatched amount
- WHEN the notification is processed
- THEN the order MUST NOT be marked paid automatically

#### Scenario: Superseded attempt does not pay
- GIVEN an `APPROVED` notification for a superseded attempt
- WHEN the notification is processed
- THEN the order MUST NOT transition

### Requirement: Remote checkout cancellation

After the local transaction commits, the system MUST attempt to cancel the superseded remote checkout with its own stable `X-Idempotency-Key`, MUST NOT hold the database transaction open during the remote call, and MUST keep the local consistency guarantees independent of the remote result.

#### Scenario: Successful remote cancellation preserves history
- GIVEN a superseded attempt with a remote checkout
- WHEN cancellation succeeds
- THEN the provider cancellation result MUST be recorded
- AND the attempt MUST remain as history

#### Scenario: Already cancelled is idempotent success
- GIVEN the provider reports the checkout was already cancelled
- WHEN cancellation is processed
- THEN it MUST be treated as an idempotent success
- AND no unnecessary error MUST be propagated

#### Scenario: Remote cancellation no longer possible
- GIVEN the provider no longer allows cancellation
- WHEN cancellation is processed
- THEN `version` MUST NOT be reverted, the mutation MUST NOT be reverted and the attempt MUST remain superseded

#### Scenario: Cancellation timeout is retryable
- GIVEN local commit succeeded and the cancellation call failed with a timeout or 5xx
- WHEN the failure is recorded
- THEN the attempt MUST remain superseded with a retryable cancellation status
- AND cancellation MUST be retryable independently without repeating the order mutation

### Requirement: Version barrier

The webhook MUST NOT mark an order paid unless the approved attempt matches the order's current version and amount. `Order.version` plus webhook validation MUST be the definitive consistency barrier even when remote cancellation fails.

#### Scenario: Old checkout approved by race
- GIVEN a checkout for an older version is approved after the order was modified
- WHEN the notification is processed
- THEN the order MUST NOT be paid
- AND the attempt MUST be recorded as approved and superseded

### Requirement: Payment attempt identity

Each payment attempt MUST be identifiable by provider external identifier with uniqueness per provider, and MUST NOT be assumed unique across providers.

#### Scenario: External identity uniqueness
- GIVEN two providers
- WHEN attempts store external identifiers
- THEN uniqueness MUST apply per `(provider, externalId)`
- AND an attempt without a provider response MUST be allowed to have no external identifier

### Requirement: No Outbox

The system MUST NOT introduce Outbox, Saga, Redis, distributed locks or a message broker for this flow. Local consistency MUST be provided by a single local transaction covering the order mutation, `version` increment, attempt supersede and idempotency record.

#### Scenario: Local transaction is sufficient
- GIVEN a mutation with a superseded attempt
- WHEN the transaction commits
- THEN the order mutation, `version` increment, attempt supersede and idempotency record MUST all be persisted together
- AND the external provider call MUST happen after commit

## ADDED Requirements

### Requirement: Payment capabilities exposed to conversation

The `order` module MUST expose payment checkout creation through its application ports so that `conversation` can request it via `OrderServicePort`. `conversation` MUST NOT expose or depend on a payment-specific port, and MUST NOT know about Mercado Pago.

#### Scenario: Conversation uses the order port
- GIVEN the agent requests a checkout
- WHEN the use case executes
- THEN it MUST flow through `OrderServicePort` -> `order` application -> payment provider port
- AND `conversation` MUST NOT reference Mercado Pago

### Requirement: Checkout does not block editing

A pending checkout MUST NOT block editing. Creating a checkout MUST NOT be triggered automatically after each modification; a new checkout MUST require a new explicit confirmation.

#### Scenario: Edit while a pending checkout exists
- GIVEN a `PENDING` online order with a pending, non-approved checkout
- WHEN the customer modifies the order
- THEN the order MUST be reopened, the previous attempt superseded, and the modification applied
- AND a new checkout MUST NOT be created automatically

#### Scenario: Not editable after a current approved payment
- GIVEN an approved attempt for the current version
- WHEN a modification is attempted
- THEN it MUST be rejected and a new order MUST be required
