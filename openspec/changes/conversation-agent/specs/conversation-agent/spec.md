# Conversation Agent Specification

## Purpose

A conversational agent inside the `conversation` bounded context that answers catalog and delivery questions and builds, confirms and tracks an order by orchestrating other bounded contexts through application ports. LangChain/LangGraph run only in infrastructure as a driver adapter; LangSmith/Studio is the first test driver.

## Requirements

### Requirement: Framework isolation

`conversation.domain` and `conversation.application` MUST NOT import `langchain`, `langgraph`, `langsmith`, `django` or `prisma`. Cross-module imports MUST exist only under `conversation.infrastructure.adapters` and MUST target sibling `application.ports` only.

#### Scenario: No framework leaks inward
- GIVEN the conversation module
- WHEN import-linter runs
- THEN the framework contract and the narrowed cross-module whitelist MUST pass

#### Scenario: Application depends only on its own ports
- GIVEN a change that makes `conversation.application` import `order.application` directly
- WHEN import-linter runs
- THEN the check MUST fail

### Requirement: Trusted execution context

The system MUST resolve a trusted `AgentExecutionContext` containing `business_configuration_id`, `conversation_id`, `client_id`, `channel` and optional `external_thread_id` BEFORE executing any tool. Tool inputs MUST NOT override these values.

#### Scenario: Model cannot choose the business
- GIVEN a tool call whose arguments include another business identifier
- WHEN the tool executes
- THEN the context business identifier MUST be used
- AND the model-supplied value MUST be ignored

### Requirement: Thread to conversation resolution

The system MUST resolve `(business_config_id, channel, external_thread_id)` to exactly one `Conversation` whose `id` is an internally generated UUID, independent from the external thread identifier.

#### Scenario: Same thread resolves to the same conversation
- GIVEN a channel thread already associated with a conversation
- WHEN a new message arrives on that thread
- THEN the existing conversation MUST be reused

#### Scenario: Different threads map to different conversations
- GIVEN two distinct external thread identifiers in the same business
- WHEN each receives a message
- THEN two distinct conversations MUST exist

### Requirement: Message persistence

The system MUST persist the incoming USER message before invoking the agent and persist the ASSISTANT message after the agent responds. Each incoming message MUST carry a stable `externalMessageId` generated once at ingress and reused across retries.

#### Scenario: User and assistant messages persisted
- GIVEN a valid incoming message
- WHEN the flow completes
- THEN a USER message and an ASSISTANT message MUST both be persisted for the conversation

#### Scenario: Retry does not duplicate the message
- GIVEN an incoming message already persisted with its `externalMessageId`
- WHEN the same message is re-processed
- THEN no additional message row MUST be created

### Requirement: No business logic in tools

Tools MUST only map input to a conversation command, execute the conversation use case with the trusted context, and serialize the result. Tools MUST NOT contain pricing, coupon, delivery, catalog-validation or order-transition rules.

#### Scenario: Thin tool
- GIVEN a tool invocation
- WHEN it executes
- THEN it MUST call exactly one conversation use case
- AND it MUST NOT import Prisma or another bounded context directly

### Requirement: Tool surface

The agent MUST expose exactly these tools: `search_products`, `get_product_detail`, `get_current_order`, `add_item`, `update_item`, `remove_item`, `quote_delivery`, `set_delivery`, `set_pickup`, `set_payment_type`, `apply_coupon`, `get_order_summary`, `confirm_order`, `cancel_order`, `get_latest_active_order`. Administrative operations MUST NOT be exposed.

#### Scenario: Administrative operations absent
- GIVEN the registered tool set
- WHEN it is inspected
- THEN it MUST NOT contain product/variant/price/ingredient/modifier CRUD, delivery zone/pricing configuration, coupon creation, `advance_order`, `set_order_status` or `reopen_order`

### Requirement: Informational questions do not create an order

Informational requests MUST NOT create or mutate an order.

#### Scenario: Menu question
- GIVEN a customer asks what products exist
- WHEN the agent responds
- THEN it MUST use `search_products`
- AND no order MUST be created

#### Scenario: Product detail question
- GIVEN a customer asks what a product contains
- WHEN the agent responds
- THEN it MUST use `get_product_detail`
- AND no order MUST be created

#### Scenario: Delivery availability question without an order
- GIVEN a customer asks whether delivery reaches an address and no order exists
- WHEN the agent responds
- THEN it MUST use `quote_delivery`
- AND no order MUST be created

### Requirement: Purchase intent creates or reuses the cart

Concrete purchase intent MUST create a draft order if none exists and MUST reuse the existing editable order otherwise. The backend draft is the source of truth for the cart; conversation history MUST NOT be used as cart state.

#### Scenario: First item creates the order
- GIVEN no editable order exists for the conversation
- WHEN the customer requests an item
- THEN an order MUST be created and the line added

#### Scenario: Further items reuse the same order
- GIVEN an editable order exists for the conversation
- WHEN the customer requests another item
- THEN the new line MUST be added to that same order

#### Scenario: Same variant twice is two lines
- GIVEN an editable order already contains a variant line
- WHEN the customer adds the same variant with a different configuration
- THEN a second, independent line MUST be created

### Requirement: Line identity

Line mutations MUST identify the line by `line_id`, never by `product_id` or `product_variant_id`.

#### Scenario: Update targets a specific line
- GIVEN an order with two lines of the same variant
- WHEN one line is updated
- THEN only the line with the given `line_id` MUST change

### Requirement: Modal selection and removed ingredients validation

The system MUST validate modifier selections and removed ingredients against catalog data owned by `catalog`. The agent MUST NOT decide validity.

#### Scenario: Non-removable ingredient rejected
- GIVEN an ingredient that belongs to the variant but is not removable
- WHEN the customer requests removing it
- THEN the backend MUST reject the removal with a structured business error

#### Scenario: Required modifier group not satisfied
- GIVEN a product whose modifier group requires a minimum selection
- WHEN the customer adds it without satisfying the minimum
- THEN the backend MUST reject the addition with a structured business error

### Requirement: Delivery configuration

Setting delivery MUST obtain a quote from the existing `delivery` quote port and MUST configure the order only when delivery is available. Delivery pricing MUST NOT be computed inside `conversation`.

#### Scenario: Available delivery configures the order
- GIVEN a quote that is available
- WHEN the customer requests delivery to that address
- THEN the order delivery MUST be configured with the quoted cost

#### Scenario: Unavailable delivery does not configure the order
- GIVEN a quote that is unavailable
- WHEN the customer requests delivery to that address
- THEN the order MUST NOT store a valid delivery for that address

### Requirement: Payment type

`set_payment_type` MUST accept only the domain values `CASH` and `ONLINE`.

#### Scenario: Invalid payment type rejected
- GIVEN a value that is not `CASH` or `ONLINE`
- WHEN payment type is set
- THEN the backend MUST reject it

### Requirement: Coupon application

Applying a coupon MUST delegate validation and discount computation to the backend. The agent MUST NOT compute discounts or assert coupon validity.

#### Scenario: Invalid coupon returns a business error
- GIVEN a coupon that the backend rejects
- WHEN the customer applies it
- THEN a structured business error MUST be returned

### Requirement: Order summary

`get_order_summary` MUST return a backend-sourced summary including order id, status, lines, subtotal, discount, shipping cost, total, delivery type, address, payment type and missing requirements.

#### Scenario: Summary reflects the backend
- GIVEN a draft with lines, delivery and payment type
- WHEN the summary is requested
- THEN every amount MUST come from the backend
- AND missing requirements MUST reflect real order rules

### Requirement: Explicit confirmation

`confirm_order` MUST be called only after the current summary has been presented to the customer and the customer has explicitly confirmed that summary. A generic affirmative answer to a different question MUST NOT trigger confirmation.

#### Scenario: Confirmation after summary
- GIVEN the summary was presented and the customer explicitly confirms it
- WHEN the agent acts
- THEN `confirm_order` MUST be called

#### Scenario: Affirmative without summary
- GIVEN the agent asked an unrelated yes/no question
- WHEN the customer answers affirmatively
- THEN `confirm_order` MUST NOT be called

#### Scenario: Retry is idempotent
- GIVEN an order already confirmed successfully
- WHEN the same confirmation is retried
- THEN the current confirmed state MUST be returned with no additional effect

### Requirement: Cancellation

`cancel_order` MUST delegate cancellability entirely to `order`. The agent MUST NOT decide whether a state is cancellable.

#### Scenario: Not cancellable returns a business error
- GIVEN an order in a state that the backend does not allow cancelling
- WHEN cancellation is requested
- THEN a structured business error MUST be returned

#### Scenario: Cancel retry is idempotent
- GIVEN an order already cancelled
- WHEN the same cancellation is retried
- THEN an idempotent success MUST be returned

### Requirement: Latest active order

`get_latest_active_order` MUST be resolved by the backend scoped to the current business and client (and conversation when applicable). The agent MUST NOT list orders and guess.

#### Scenario: No cross-restaurant leakage
- GIVEN active orders in two businesses
- WHEN the latest active order is requested for one business
- THEN only an order from that business MUST be returned

### Requirement: Nothing invented from state

The agent MUST NOT state prices, availability, ingredients, modifier options, coupon validity, delivery availability, shipping costs, order totals or order status from memory. Any such value MUST come from a tool result.

#### Scenario: State-dependent answer uses a tool
- GIVEN a question about price, availability, delivery, shipping, order or status
- WHEN the agent responds
- THEN the value MUST originate from a tool result

### Requirement: Business vs technical errors

The system MUST distinguish business outcomes from technical failures. A technical failure MUST NOT be presented to the customer as a business outcome.

#### Scenario: Provider failure is not "outside zone"
- GIVEN the delivery provider fails technically
- WHEN the agent responds
- THEN it MUST NOT state that the address is outside the delivery zone

### Requirement: New order required

When the current order is not editable, the backend MUST report `NEW_ORDER_REQUIRED` and MUST NOT create a new order implicitly. `conversation` MUST ask the customer before starting a new order.

#### Scenario: Closed previous order
- GIVEN the previous order for the conversation is paid
- WHEN the customer requests an item
- THEN the backend MUST report `NEW_ORDER_REQUIRED`
- AND the previous order MUST remain unchanged
- AND the agent MUST ask the customer before creating a new order
