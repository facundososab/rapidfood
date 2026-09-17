# Catalog Query Specification

## Purpose

Catalog query capabilities required by the conversational agent: text search combined with the existing category and availability filters, plus a product detail projection rich enough for the agent to answer variant price, ingredient and modifier questions in one call.

## Requirements

### Requirement: Product search

The product listing MUST support a text `search` filter combined with the existing `category_id` and `available` filters, scoped to a single business.

#### Scenario: Search by text
- GIVEN products exist in the catalog
- WHEN the listing is requested with a search term
- THEN only products matching the term in their name or description MUST be returned

#### Scenario: Combined filters
- GIVEN a category and an availability filter
- WHEN the listing is requested with a search term and both filters
- THEN all three constraints MUST apply together

#### Scenario: Business isolation
- GIVEN products in more than one business
- WHEN the listing is requested for one business
- THEN only products of that business MUST be returned

### Requirement: Rich product detail

The product detail projection MUST include the product identity, description, availability, its variants with current price and availability, each variant's ingredients with the removable flag, and the modifier groups with their minimum/maximum selections and options with `price_delta` and availability.

#### Scenario: Single call detail
- GIVEN an existing product with variants, ingredients and modifier groups
- WHEN `get_product_detail` is requested
- THEN the response MUST include all of those projections
- AND the agent MUST NOT need multiple requests to reconstruct the product

#### Scenario: Current price per variant
- GIVEN a variant with a price history
- WHEN its detail is requested
- THEN the current effective price MUST be returned

### Requirement: Administrative price endpoints are not tools

Variant price endpoints MUST remain administrative and MUST NOT be exposed to the agent. The agent MUST obtain prices only through catalog queries.

#### Scenario: No price mutation from the agent
- GIVEN the registered agent tool set
- WHEN it is inspected
- THEN it MUST NOT contain any variant price read/write tool
- AND current price MUST be obtained through the product detail projection
