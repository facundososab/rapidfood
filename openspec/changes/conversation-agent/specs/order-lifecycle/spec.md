# Order Lifecycle Specification

## Purpose

Order lifecycle rules for `order`: a monotonic commercial version, an explicit reopen transition for online orders awaiting payment, centralized state transitions, and a pure current-order resolution used by the conversational agent.

## Requirements

### Requirement: Centralized state transitions

The `order` domain MUST be the single source of truth for allowed order transitions, including payment-type conditions and the cancellable state set. `ConfirmOrderUseCase`, `CancelOrderUseCase`, `AdvanceStateUseCase` and `UpdateOrderStatusUseCase` MUST delegate to it and MUST NOT define their own transition maps.

#### Scenario: Single source verified
- GIVEN the order module
- WHEN transition rules are inspected
- THEN exactly one centralized definition MUST exist
- AND no use case or adapter MUST declare a competing map

#### Scenario: Online payment approval
- GIVEN an order in `PENDING` with `paymentType == ONLINE`
- WHEN the payment is approved
- THEN the order MUST transition to `PAID`

#### Scenario: Cash acceptance
- GIVEN an order in `PENDING` with `paymentType == CASH`
- WHEN the business accepts the order
- THEN the order MUST transition to `CONFIRMED`

#### Scenario: Payment-type conditions enforced
- GIVEN an order in `PENDING`
- WHEN a transition to `PAID` is requested with `paymentType == CASH`, or a transition to `CONFIRMED` is requested with `paymentType == ONLINE`
- THEN the transition MUST be rejected

### Requirement: Cancellation rules

Normal cancellation MUST be allowed only from `DRAFT`, `PENDING`, `PAID` and `CONFIRMED`, and MUST NOT be allowed from `IN_PREPARATION`, `READY`, `DELIVERED` or `PICKED_UP`. No administrative exception MUST bypass this in the normal cancellation path.

#### Scenario: Cancellable states
- GIVEN an order in `DRAFT`, `PENDING`, `PAID` or `CONFIRMED`
- WHEN cancellation is requested
- THEN the order MUST become `CANCELLED`

#### Scenario: Non-cancellable after preparation
- GIVEN an order in `IN_PREPARATION`, `READY`, `DELIVERED` or `PICKED_UP`
- WHEN cancellation is requested through the normal path
- THEN it MUST be rejected

#### Scenario: Idempotent cancellation retry
- GIVEN an order already `CANCELLED`
- WHEN cancellation is retried with the same logical intent
- THEN an idempotent success MUST be returned

#### Scenario: Exceptional admin cancellation is out of scope
- GIVEN a need to cancel after preparation started
- WHEN cancellation is required
- THEN it MUST NOT be handled by the normal path
- AND it MUST require a separate future use case with its own authorization

### Requirement: Commercial version

`Order` MUST expose a monotonic `version` incremented whenever the commercial snapshot changes: add item, update item, remove item, coupon change, delivery address change affecting shipping, and `DELIVERY <-> PICKUP` changes. The rule MUST be centralized and MUST NOT be applied ad hoc by controllers.

#### Scenario: Version increments on item change
- GIVEN an order at `version = N`
- WHEN an item is added, updated or removed
- THEN `version` MUST become `N + 1`

#### Scenario: Version increments on fulfillment change
- GIVEN an order at `version = N`
- WHEN delivery/pickup or the shipping-affecting address changes
- THEN `version` MUST become `N + 1`

### Requirement: Explicit reopen for modification

The system MUST preserve `modifiable <=> status == DRAFT` and MUST provide an explicit `reopen_for_modification()` transition from `PENDING` to `DRAFT`, allowed only when `paymentType == ONLINE` and no `PaymentAttempt` for the current `version` is approved and not superseded. Reopening MUST clear `confirmedAt`.

#### Scenario: Reopen allowed with pending checkout
- GIVEN a `PENDING` order with `paymentType == ONLINE` and no approved attempt for the current version
- WHEN `reopen_for_modification()` is invoked
- THEN the order MUST become `DRAFT`
- AND `confirmedAt` MUST be cleared

#### Scenario: Rejected when a current attempt is approved
- GIVEN a `PENDING` order with an approved, non-superseded attempt for the current version
- WHEN `reopen_for_modification()` is invoked
- THEN it MUST be rejected

#### Scenario: Rejected for cash
- GIVEN a `PENDING` order with `paymentType == CASH`
- WHEN `reopen_for_modification()` is invoked
- THEN it MUST be rejected

#### Scenario: Reopening invalidates the previous confirmation
- GIVEN a reopened order
- WHEN a new checkout is requested before confirming again
- THEN it MUST be rejected
- AND a new explicit confirmation MUST be required first

### Requirement: Reopen-aware mutations

Mutations MUST apply reopen atomically: claim the idempotency key, load and lock the order, reopen when allowed (superseding the current attempt), mutate, increment `version`, persist the result, and commit in a single transaction. Reopen MUST NOT be exposed as an agent tool.

#### Scenario: Mutation reopens and modifies atomically
- GIVEN a `PENDING` online order with a pending checkout and no approved attempt
- WHEN a line is added
- THEN the order MUST be reopened to `DRAFT`, the attempt MUST be superseded, the line added, `version` incremented and the result persisted in one transaction

#### Scenario: Not editable is not mutated
- GIVEN a paid order
- WHEN a mutation is attempted
- THEN `NEW_ORDER_REQUIRED` MUST be returned
- AND the order MUST remain unchanged

### Requirement: Pure current-order resolution

`get_current_order` MUST be a read-only query that returns the current order plus editability metadata (`editable`, `requiresReopenForModification`, `requiresNewOrder`) and MUST NOT create, reopen or otherwise mutate any order.

#### Scenario: Draft is editable
- GIVEN the current order is `DRAFT`
- WHEN `get_current_order` is requested
- THEN `editable = true`, `requiresReopenForModification = false`, `requiresNewOrder = false`
- AND the order MUST NOT change

#### Scenario: Pending online is reopenable
- GIVEN the current order is `PENDING` with `paymentType == ONLINE` and no approved attempt for the current version
- WHEN `get_current_order` is requested
- THEN `editable = true`, `requiresReopenForModification = true`, `requiresNewOrder = false`
- AND the order MUST NOT change

#### Scenario: Pending cash requires a new order
- GIVEN the current order is `PENDING` with `paymentType == CASH`
- WHEN `get_current_order` is requested
- THEN `editable = false` and `requiresNewOrder = true`

#### Scenario: Advanced or paid states require a new order
- GIVEN the current order is `PAID`, `CONFIRMED`, `IN_PREPARATION`, `READY`, `DELIVERED` or `PICKED_UP`, or has an approved attempt for the current version
- WHEN `get_current_order` is requested
- THEN `editable = false` and `requiresNewOrder = true`

#### Scenario: Cancelled is not reused
- GIVEN the current order is `CANCELLED`
- WHEN a new purchase intent arrives
- THEN a new `DRAFT` MUST be required

### Requirement: Modification resolution never creates orders

`resolve_order_for_modification` MUST return the editable order, perform a permitted reopen, or return `CURRENT_ORDER_NOT_EDITABLE` / `NEW_ORDER_REQUIRED`. It MUST NOT create a new order; new-order creation MUST use the normal draft creation flow driven by `conversation`.

#### Scenario: Resolution does not create
- GIVEN a conversation whose previous order is paid
- WHEN `resolve_order_for_modification` is invoked
- THEN `NEW_ORDER_REQUIRED` MUST be returned
- AND no order MUST be created

### Requirement: Latest active order

The system MUST resolve the latest active order scoped to the current business and client (and conversation when applicable), without requiring the caller to list and choose.

#### Scenario: Scoped resolution
- GIVEN orders in multiple businesses
- WHEN the latest active order is requested for one business
- THEN only an order belonging to that business MUST be returned

### Requirement: Fulfillment configuration

The system MUST support configuring delivery and pickup, and setting the payment type to `CASH` or `ONLINE` only, updating the commercial version when the commercial snapshot changes.

#### Scenario: Pickup clears delivery data
- GIVEN a draft with a delivery address and shipping cost
- WHEN pickup is selected
- THEN the delivery data MUST be cleared and the version incremented

#### Scenario: Payment type values
- GIVEN a payment type other than `CASH` or `ONLINE`
- WHEN it is set
- THEN it MUST be rejected
