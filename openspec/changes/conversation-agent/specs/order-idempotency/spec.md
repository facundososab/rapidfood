# Order Idempotency Specification

## Purpose

Channel-neutral, atomic idempotency for order mutations that are not naturally idempotent, reusable by LangChain, WhatsApp, HTTP and future channels.

## Requirements

### Requirement: Neutral idempotency concept

The system MUST provide an `IdempotentOperation` concept that is not coupled to any specific channel or agent technology, with a unique constraint on `(businessConfigId, idempotencyKey)`.

#### Scenario: Channel-independent
- GIVEN the idempotency concept
- WHEN it is used by a channel
- THEN it MUST NOT reference LangChain, LangSmith or any agent-specific identifier

### Requirement: Logical key

The idempotency key MUST be derived from `businessConfigId`, `conversationId`, `externalMessageId`, `operationName` and a canonical hash of the arguments, where the canonical hash MUST be computed over canonicalized JSON so property order does not change the hash. `run_id` MUST NOT participate.

#### Scenario: Argument order does not change the key
- GIVEN the same arguments serialized with different property order
- WHEN the canonical hash is computed
- THEN the key MUST be identical

#### Scenario: Different operations do not collide
- GIVEN the same message triggers `add_item` and `set_delivery`
- WHEN both are executed
- THEN they MUST NOT collide on the same key

### Requirement: Atomic claim

Claiming the idempotency key, performing the business mutation and persisting the operation result MUST happen in a single PostgreSQL transaction. Splitting the claim from the mutation MUST NOT be allowed.

#### Scenario: Claim and mutation commit together
- GIVEN a mutation is executed
- WHEN an intermediate failure occurs before commit
- THEN neither the claim nor the mutation MUST be persisted

#### Scenario: Stored result is replayed
- GIVEN an operation already completed for a key
- WHEN the same key is retried
- THEN the stored result MUST be returned
- AND the mutation MUST NOT run again

### Requirement: Operation identity

An `IdempotentOperation` MUST store at least an id, `businessConfigId`, `idempotencyKey`, `operationName`, status, an optional result and a creation timestamp.

#### Scenario: Result reuse
- GIVEN a completed `add_item` operation
- WHEN a retry occurs
- THEN the previously stored result (for example the same `OrderLine.id`) MUST be returned

### Requirement: Same message, same intent

The same `externalMessageId` with the same operation and arguments MUST produce a single effect. A different `externalMessageId` with the same arguments MUST produce a new legitimate effect.

#### Scenario: Retry produces one line
- GIVEN the same `externalMessageId` and the same `add_item` arguments
- WHEN the tool is retried
- THEN exactly one line MUST exist

#### Scenario: Distinct messages produce distinct effects
- GIVEN two different `externalMessageId` values with the same `add_item` arguments
- WHEN both are executed
- THEN two legitimate lines MUST exist

### Requirement: Concurrency

Concurrent executions with the same idempotency key MUST result in a single mutation. Concurrent mutations with different keys on the same order MUST NOT lose updates.

#### Scenario: Concurrent same key
- GIVEN two concurrent executions with the same idempotency key
- WHEN both complete
- THEN exactly one mutation MUST be applied

#### Scenario: Concurrent different keys
- GIVEN two concurrent mutations on the same order with different keys
- WHEN both complete
- THEN both mutations MUST be reflected
- AND no update MUST be lost

### Requirement: Semantic idempotency for confirm and cancel

`confirm_order` and `cancel_order` MUST use semantic idempotency based on order state and MUST NOT require an explicit key.

#### Scenario: Confirm retry
- GIVEN an order already confirmed successfully
- WHEN `confirm_order` is retried
- THEN the current confirmed state MUST be returned with no additional effect
- AND an incompatible state MUST fail normally

#### Scenario: Cancel retry
- GIVEN an order already `CANCELLED`
- WHEN `cancel_order` is retried
- THEN an idempotent success MUST be returned

### Requirement: Coupon application

`apply_coupon` MUST be protected by idempotency. If no natural invariant guarantees a single application, an explicit idempotency key MUST be used.

#### Scenario: Retry applies once
- GIVEN a coupon already applied for the same logical operation
- WHEN the operation is retried
- THEN the coupon MUST NOT be applied again
- AND the previously applied result MUST be returned

### Requirement: Scope of protection

Read-only operations (`search_products`, `get_product_detail`, `get_current_order`, `quote_delivery`, `get_order_summary`, `get_latest_active_order`) MUST NOT require an idempotency key.

#### Scenario: Reads are not protected
- GIVEN any read-only tool
- WHEN it executes repeatedly
- THEN no `IdempotentOperation` MUST be created
