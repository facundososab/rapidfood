# Design: Mercado Pago Payments

## Technical Approach

Implement `order-payments` inside `api/modules/order` as an order-owned capability. Domain/application stay pure; REST and Mercado Pago are edge adapters. Webhooks are provider-authoritative: the view validates signature/protocol shape, then the use case fetches Mercado Pago state before mutating local state.

## Architecture Decisions

| Topic | Alternatives | Decision / rationale |
|---|---|---|
| Bounded context | New `payment` module | Keep in `order`; payment attempts directly drive `PENDING -> PAID`, and Prisma already relates `Payment` to `Order`. |
| Provider coupling | SDK in use case | SDK only in `infrastructure/adapters/driven/mercadopago`; application sees `PaymentProvider`. |
| Webhook trust | Use raw webhook status | Never trust raw status; use `data.id`/reference to fetch authoritative remote payment. |
| Conversation | Wire WhatsApp now | Deferred; current conversation URL/container uses in-memory wiring, so expose stable order flow first. |

## Data Flow

```text
POST /api/orders/{id}/payment-link/
  -> DRF view -> CreatePaymentLinkCommand -> use case
  -> OrderRepository + PaymentRepository -> PaymentProvider.create_checkout_link()
  -> PaymentRepository.save(provider ids/link) -> response DTO

POST /api/orders/payments/mercadopago/webhook/
  -> signature validator in REST adapter -> ProcessPaymentNotificationCommand
  -> PaymentProvider.get_payment(data_id) -> status mapper
  -> PaymentRepository.update_status -> if APPROVED, OrderRepository.save(PAID)
```

## File Changes

| File | Action | Description |
|---|---|---|
| `api/modules/order/domain/models/payment_status.py` | Create | `str, Enum`: `PENDING`, `APPROVED`, `REJECTED`, `FAILED`, `EXPIRED`. |
| `api/modules/order/domain/models/payment.py` | Create | Dataclass entity: id, order_id, provider, amount, status, external_id, preference_id, checkout_url, external_reference, expires_at. |
| `api/modules/order/application/ports/driver/payment_ports.py` | Create | Commands/results for link creation and notification processing. |
| `api/modules/order/application/ports/driven/payment_repository.py` | Create | Port: create pending, find by id/external/preference/reference, update provider data/status. |
| `api/modules/order/application/ports/driven/payment_provider.py` | Create | Port DTOs: create link and fetch remote payment. Capabilities, not Mercado Pago names. |
| `api/modules/order/application/use_cases/*payment*_use_case.py` | Create | Orchestration and invariants only. |
| `api/shared/infrastructure/prisma/schema.prisma` | Modify | Add `preferenceId`, `checkoutUrl`, `externalReference`, `providerPayload`, `expiresAt`; add indexes/unique where safe for `externalId`, `preferenceId`, `externalReference`. |
| `api/modules/order/infrastructure/adapters/driven/prisma/payment_repository.py` + `mappers/payment_mapper.py` | Create | Prisma queries and mapping; mapper isolated from use cases. |
| `api/modules/order/infrastructure/adapters/driven/mercadopago/*` | Create | SDK adapter, settings/env loader, status mapper, provider exceptions. |
| `api/modules/order/infrastructure/adapters/driver/rest/{serializers.py,views.py,urls.py}` | Modify | Add payment-link and webhook endpoints; serializers only validate protocol shape. |
| `api/modules/order/configuration/container.py`, `api/composition/container.py` | Modify | Explicitly wire repositories/provider/use cases; no service locator. |
| `pyproject.toml` | Modify | Add `mercadopago` dependency only when implementing adapter. |

## Interfaces / Contracts

Application DTOs are dataclasses matching project style: `CreatePaymentLinkCommand(order_id)`, `CreatePaymentLinkResult(order_id,payment_id,provider,checkout_url,status)`, `ProcessPaymentNotificationCommand(provider,data_id,topic,raw_payload,headers)`, `ProcessPaymentNotificationResult(payment_id,status,order_id,order_status,processed)`.

`CreatePaymentLinkUseCase`: load order; require exists, `PENDING`, `ONLINE`, `total_amount > 0`; create local `Payment(PENDING)`; call provider with amount/external_reference/order data; persist provider identifiers/link; return plain result.

`ProcessPaymentNotificationUseCase`: fetch remote payment; locate local payment by `external_id`, `preference_id`, or `external_reference`; map status; if already final with same status, return processed without repeating effects; update payment; if `APPROVED` and order is `PENDING`, set `PAID`; non-approved keeps order `PENDING`.

Mercado Pago adapter uses SDK preference create (`init_point`, `id`, `external_reference`, `notification_url`) and payment get (`status`, `external_reference`, `transaction_amount`). Signature validation stays in REST infrastructure using `x-signature`, `x-request-id`, `data.id`, HMAC-SHA256 manifest; missing secret means validation disabled only by explicit settings default.

## Testing Strategy

| Order | Layer | Tests |
|---|---|---|
| 1 | Domain | `PaymentStatus`, `Payment` final/idempotent helpers if added. |
| 2 | Use case unit | Link creation success and invalid order cases with mocks/fakes. |
| 3 | Use case unit | Webhook approved/non-approved/duplicate/provider-authoritative cases. |
| 4 | Mapper/repository integration | Prisma payment fields, lookup indexes, status updates with `db` fixture. |
| 5 | Adapter unit | Mercado Pago status mapper, SDK error translation, signature validation. |
| 6 | REST | Endpoint delegates, status codes, invalid signature rejection. |
| 7 | Architecture | `uv run lint-imports`; update contracts to also forbid `mercadopago` inward and fix stale/incorrect adapter paths. |

## Migration / Rollout

Create Prisma migration for nullable provider trace fields before repository tests. Existing rows remain valid. Rollback removes routes/wiring/adapters/use cases and reverts the migration if no downstream dependency exists.

## Open Questions

- [ ] Confirm production currency/locale for Mercado Pago preference payload.
- [ ] Decide whether sandbox webhook signature is mandatory in local development or explicitly disabled by env.
