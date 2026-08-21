# Delta for Conversations

## ADDED Requirements

### Requirement: Conversation Domain Model

The conversation module MUST model `Conversation` and `Message` as pure domain objects with no Django, DRF, Prisma, or web imports. Conversation MUST include `conversationId`, `overallSentiment`, `lastIntent`, and `channel`; Message MUST include `messageId`, `role`, `content`, `detectedIntent`, `sentiment`, and `status`. Every persisted message MUST belong to exactly one conversation.

#### Scenario: Message belongs to conversation

- GIVEN a conversation exists
- WHEN a user or assistant message is recorded
- THEN the message is linked to that conversation
- AND no framework or persistence type leaks into the domain object

### Requirement: Conversation Upsert by Channel Identity

The application MUST retrieve or create a conversation by client/channel identity through ports and return plain DTOs. Channel identity MUST be stable enough to resume abandoned draft context.

#### Scenario: Existing conversation is reused

- GIVEN a client sends a message from an already-known channel identity
- WHEN the upsert use case runs
- THEN the existing conversation is returned

#### Scenario: Unknown identity creates conversation

- GIVEN no conversation exists for the channel identity
- WHEN the upsert use case runs
- THEN a new conversation associated with that identity is returned

### Requirement: Message Recording and Listing

The module MUST record inbound and assistant messages and MUST list conversation history in deterministic order through application ports.

#### Scenario: List recorded messages

- GIVEN multiple messages exist for a conversation
- WHEN the list messages query runs
- THEN it returns only that conversation's messages in chronological order

### Requirement: Webhook Receive Orchestration

The webhook driver adapter MUST validate HTTP payload shape, translate it to a use-case command, and return a plain HTTP response. The use case MUST store the user message, detect intent, store the assistant response, and return a plain response DTO.

#### Scenario: Valid inbound webhook

- GIVEN a valid channel identity and message content
- WHEN the webhook is received
- THEN the user message and assistant response are stored
- AND the HTTP response contains only transport-safe data

#### Scenario: Invalid inbound webhook

- GIVEN the payload lacks required identity or content
- WHEN the webhook is received
- THEN no message is stored
- AND a validation error response is returned

### Requirement: Deterministic Intent Detection Port

Intent detection MUST be consumed through a driven port and the first implementation MUST be deterministic. The conversation application MUST NOT depend directly on an LLM, prompt, SDK, or external AI service.

#### Scenario: Intent is detected through port

- GIVEN a message saying the client wants to order
- WHEN the receive use case processes it
- THEN it obtains an order-related intent from the intent detector port

### Requirement: Draft Order Orchestration Through Ports

For order-related intents, conversation MUST call client, order, catalog, and configuration/coupon ports only. It MUST NOT import other modules' storage, adapters, ORM models, or repositories.

#### Scenario: Build draft through order port

- GIVEN an order-related message mentions products
- WHEN the receive use case handles it
- THEN product lookup and draft changes occur only through ports

### Requirement: Existing Active Draft Disambiguation

If an active non-expired `BORRADOR` exists for the conversation and the client starts a new order, the assistant response MUST ask whether to continue the draft or start over.

#### Scenario: Draft already exists

- GIVEN a conversation has one active `BORRADOR`
- WHEN the client asks to start a new order
- THEN no draft is silently reused or abandoned
- AND the assistant asks for a continue-or-start-over choice

### Requirement: Explicit Confirmation Boundary

Conversation MUST NOT transition `BORRADOR` to `PENDIENTE` unless the client explicitly confirms. Confirmation MUST be requested through the order port so order owns validation, price freezing, totals, and estimated time.

#### Scenario: Missing explicit confirmation

- GIVEN a draft order is complete
- WHEN the client has not explicitly confirmed it
- THEN conversation does not call order confirmation

#### Scenario: Explicit confirmation

- GIVEN a draft order exists and the client explicitly confirms
- WHEN the receive use case handles the confirmation
- THEN it requests confirmation through the order port

### Requirement: Strict TDD Verification

Conversation behavior MUST be testable before implementation: domain invariant tests use pure objects, use-case tests use fake ports, and adapter/endpoint tests verify HTTP translation. Verification SHOULD include `uv run pytest`, `uv run lint-imports`, and `uv run python manage.py check` after implementation.

#### Scenario: Use-case tested with fakes

- GIVEN fake ports for repositories, intent, order, client, catalog, and config
- WHEN receive-message orchestration is tested
- THEN no real database, Django request, or LLM is required
