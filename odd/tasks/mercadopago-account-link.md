# Feature: mercadopago-account-link

Allow the restaurant ADMIN to link a Mercado Pago account directly from the
configuration view (Notion task 3e25961aad4680f39125ef5d308f8df5). The linked
credentials feed the existing payment flow (create link + webhook lookup) with
fallback to the global env access token.

## Context

- Notion task (Not started, Priority Baja): "Después de implementar el modulo de
  Auth hacer que se pueda vincular mercado pago directamente desde configuración".
- The Auth module (staff + Supabase) is already implemented and closed
  (`feat/supabase-auth`); this feature builds on it.
- Mercado Pago payments already exist (`order` module) using a single global env
  token (`MERCADOPAGO_ACCESS_TOKEN` → `MercadoPagoSettings.from_env()`).
- The admin panel (`ui/`) configuration view has tabs general / address /
  delivery; no payment/link section exists.
- No per-business MP credentials model exists in `schema.prisma`, and no OAuth
  "Connect your account" flow is implemented.

## Scope (confirmed with the user)

1. **Full flow**: the linked credentials are used by the existing payment flow
   (create checkout link, webhook payment lookup) with fallback to the env token.
2. **Access**: only role `ADMIN` can see and operate the MP link section.

## Design decisions

- **D1 — New Prisma model `MercadoPagoCredential`.** One row per business
  (unique `business_config_id`), storing `access_token`, `refresh_token`,
  `user_id`, `public_key`, `live_mode`. Tokens are encrypted at rest (Fernet
  with `MERCADOPAGO_TOKEN_ENCRYPTION_KEY`, derived from `DJANGO_SECRET_KEY` when
  unset). Hand-written migration SQL (no local DB), regenerate client.
- **D2 — New hexagonal module `api/modules/mercadopago/`.** Owns the OAuth
  connect flow: domain (`MercadoPagoCredential`, `MercadoPagoOAuthState`,
  errors), driver ports (get authorization URL, link account, get status,
  unlink), driven ports (`MercadoPagoCredentialRepository`,
  `MercadoPagoOAuthClient`), use cases, Prisma adapter with mapper + encryption,
  OAuth HTTP adapter, REST driver, container.
- **D3 — OAuth flow (Connect your account).**
  `GET /api/mercadopago/authorize/` → signed `state` + authorization URL to
  `https://auth.mercadopago.com/authorization?client_id=...&response_type=code&platform_id=mp&redirect_uri=...&state=...`.
  `GET /api/mercadopago/callback/?code=...&state=...` (public, AllowAny) →
  validate signed state, exchange code at `/oauth/token`, upsert credential,
  redirect to panel. `GET /api/mercadopago/status/` → linked status.
  `POST /api/mercadopago/unlink/` → delete credential.
- **D4 — Order module resolves per-business tokens.** New driven port
  `PaymentCredentialsQuery` in `order` (`get_access_token(business_config_id)`)
  wired in the composition root to the mercadopago module. `CreatePaymentLinkUseCase`
  passes the resolved token; webhook `ProcessPaymentNotificationUseCase` resolves
  from the payment's order business config, falling back to env settings.
- **D5 — Panel UI section.** New tab "Pagos / Mercado Pago" in configuration:
  link/unlink buttons + status card, rendered only when session staff role is
  `ADMIN`. HTTP client methods `get_mercadopago_status`, `link_mercadopago`,
  `unlink_mercadopago`; mock returns a neutral non-linked state.
- **D6 — Env vars:** `MERCADOPAGO_CLIENT_ID`, `MERCADOPAGO_CLIENT_SECRET`,
  `MERCADOPAGO_REDIRECT_URI`, `MERCADOPAGO_TOKEN_ENCRYPTION_KEY` (optional),
  `MERCADOPAGO_AUTH_BASE_URL` (default `https://auth.mercadopago.com`).
  Documented in `.env.example`; forwarded in `docker-compose.yml`.
- **D7 — Tests:** unit tests for use cases (fakes), adapter tests (fake OAuth
  HTTP via monkeypatch/requests), rest view tests, panel view tests, import-linter.

## Tasks (work units, one commit each)

1. **Setup** — branch `feat/mercadopago-link`; feature doc; extend `.env.example`
   with MP OAuth vars; forward env in docker-compose.
2. **Prisma model** — `MercadoPagoCredential` (unique `businessConfigId`,
   encrypted access/refresh token, userId, publicKey, liveMode, timestamps);
   hand-written migration SQL; regenerate client.
3. **Module domain + ports** — `MercadoPagoCredential`, OAuth state, errors;
   driven ports `MercadoPagoCredentialRepository` + `MercadoPagoOAuthClient`;
   driver ports for the four operations.
4. **Use cases + tests** — build_authorization_url, link_account, get_status,
   unlink_account with unit tests (fakes).
5. **Infrastructure** — Prisma credential repository + mapper + Fernet crypto;
   OAuth HTTP client adapter (requests, fake-able); container.
6. **REST** — authorize, callback, status, unlink views + urls + tests.
7. **Order integration** — `PaymentCredentialsQuery` driven port; wire adapter
   in composition root; use resolved token in CreatePaymentLinkUseCase and
   ProcessPaymentNotificationUseCase + tests.
8. **Panel UI** — configuration tab + link/unlink/status views; client
   interface + http + mock; template section gated to ADMIN; panel tests.
9. **Closure** — full pytest suite, import-linter green, docs (README + plan),
   Notion task update, one conventional commit per unit.

## Status

**In progress.** Branch `feat/mercadopago-link` — task 1 done/… (fill per unit).