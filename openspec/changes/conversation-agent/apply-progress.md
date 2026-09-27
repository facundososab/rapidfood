# Apply Progress: Conversation Agent (FINAL)

## Status

| Phase | State |
|---|---|
| 0 Foundations | done |
| 1 Order core (version, reopen, transitions, idempotency, 5 mutations) | done |
| 2 PaymentAttempt + Mercado Pago Orders API + webhook | done |
| 3 Order completion (pickup, summary, current/latest reads, endpoints) | done |
| 4 Catalog search | done |
| 5 Conversation application (context, ports, use cases, thread resolution) | done |
| 6 Conversation infrastructure (cross-module adapters + wiring) | done |
| 7 LangChain driver + tools + prompt + Studio entrypoint | done |
| 8 Tests, gates, docs, report | done |

## Final gates

| Gate | Result |
|---|---|
| `uv run pytest` | 464 passed, 0 failed |
| `uv run import-linter lint --config ../pyproject.toml` (from `api/`) | 10 kept, 0 broken |
| `uv run python manage.py check` | no issues |
| `uv run prisma validate` | valid |

## End-to-end evidence (real backend)

- `POST /api/conversation/agent/message/` with "¿Qué hamburguesas tienen?" ->
  the agent called `search_products` and answered with real catalog data.
- Same thread, "Quiero 1 Classic Burger Simple, lo paso a buscar y pago en efectivo"
  -> `add_item` + `set_pickup` + `get_order_summary` produced a DRAFT with 1 line,
  `deliveryType = PICKUP`, `origin = AGENT`, and 4 persisted messages; the agent
  asked for explicit confirmation instead of confirming on its own.
- `origin = AGENT` was a real bug found by this verification (the draft was being
  created IN_PLACE) and is now fixed + covered by a test.

## Repairs to pre-existing defects (required for a green baseline)

1. Migration history was not replayable from scratch (`20260903163938` re-added
   `coupon.is_active`/`min_order_amount`; `20260906105500` had a duplicated
   `ADD COLUMN` block). Fixed; dev-DB checksums re-stamped; replay validated on a
   scratch database.
2. The Prisma `db` fixture was out of scope for `api/modules/**` tests, which
   silently hit the DEV database. Added `api/conftest.py`.
3. Payment-provider error lived in infrastructure while a use case imported it
   (layer violation) -> moved to the port.
4. The catalog adapter imported the catalog **domain** model -> import-linter
   caught it; now it uses the public port only.
5. `MercadoPagoSettings.from_env` required an env var absent locally, hard-failing
   container construction -> defaults to "".
6. `external_message_id` was used directly as the `Message` UUID primary key ->
   now a valid UUID (deterministic UUIDv5 when the channel id is not a UUID).
7. The agent endpoint leaked a 500 HTML traceback when the model failed -> now a
   clean 502 without details.

## Known limitations

- **Gemini free tier**: 20 requests/day for `gemini-3.6-flash`; the live evals and
  multi-turn demos exhaust it quickly. The deterministic suite does not need it.
- **Mercado Pago Orders API**: the exact payload/response fields were not
  validated against live credentials; parsing is defensive (documented in the
  adapter).
- **Observed LLM behaviour**: in one run the model narrated a payment method
  without `set_payment_type` landing (`paymentType` stayed null). The tool mapping
  is correct and covered by tests; the eval scenario set exists to catch this
  class of drift once quota allows running it.
- `set_pickup` exists as a tool/use case; the panel's own pickup path still uses
  the original `ConfigureOrderUseCase`.
- The deterministic scaffold use cases (`receive_message`, intent detector) remain
  wired to the legacy webhook; they are not used by the agent flow.
