# Feature: supabase-staff-auth

Staff authentication for the restaurant (ADMIN / CASHIER / KITCHEN) using Supabase Auth as the identity provider, with email+password. Customers never authenticate.

## Context

- Stack: Django 5 + DRF is the inbound HTTP shell only; Prisma Client Python owns the data layer (PostgreSQL).
- Today there is zero auth: `DEFAULT_AUTHENTICATION_CLASSES: []`, `AllowAny` global, no sessions, no User model.
- Consumers of the protected API: the `ui/` admin panel (server-rendered Django templates, `signed_cookies` sessions).
- Public consumers: `/health/`, MercadoPago webhook, conversation/bot endpoints, payment links.
- Notion task: implement auth module (scope confirmed with the user: staff login, email+password, roles ADMIN/CAJA/COCINA, customers not authenticated).

## Design decisions

- **D1 — Supabase Auth as identity provider only.** GoTrue issues JWTs (email+password flow). Django validates the Bearer token (HS256 with `SUPABASE_JWT_SECRET`) on every request. The database stays in the Prisma-owned Postgres. No RLS/PostgREST, no data migration to Supabase.
- **D2 — Staff and roles live in our DB (Prisma).** New `Staff` model + `StaffRole` enum (`ADMIN`, `CASHIER`, `KITCHEN`) with unique `supabaseAuthId`. The role is read from our table, never from JWT claims (JWT claims are stale by design).
- **D3 — Cross-cutting DRF authentication.** `api/shared/infrastructure/auth/` owns `SupabaseJWTAuthentication` (validates JWT → principal with `supabase_auth_id`). Global default: `IsAuthenticated` + staff lookup permission (`IsStaffMember`) that resolves the `Staff` row by `supabase_auth_id` and 403s if missing. Public views opt out with `AllowAny`.
- **D4 — Public endpoints (AllowAny):** `/health/`, MercadoPago webhook, payment-link flows, conversation/bot endpoints. Everything administrative is protected by default (business, config_coupon, delivery, client, catalog, orders REST consumed by the panel).
- **D5 — Panel login via GoTrue REST.** `ui/` POSTs to `<SUPABASE_URL>/auth/v1/token?grant_type=password` with the anon key, stores the access token in the signed-cookie session, middleware requires login (except login/logout), the HTTP client forwards `Authorization: Bearer`.
- **D6 — Staff bootstrap via management command.** `create_staff` uses the Supabase admin API (service role key) to create the auth user, then inserts the `Staff` row with role. Manual usage documented; panel-based staff CRUD is out of scope.
- **D7 — Env vars:** `SUPABASE_URL`, `SUPABASE_ANON_KEY`, `SUPABASE_JWT_SECRET`, `SUPABASE_SERVICE_ROLE_KEY` (optional, only for `create_staff`). Documented in `.env.example`.
- **D8 — Testing:** JWT signed with a test secret (HS256), fake verifier, per-view tests. Existing pytest suite stays green (affected view tests are updated when an endpoint becomes protected).
- **D9 — Scope limits:** customers never authenticate; no data migration to Supabase; no RLS; no self-registration (sign-ups disabled or admin-created users only); staff CRUD in the panel is a follow-up.

## Tasks (work units, one commit each)

1. **Setup** — branch `feat/supabase-auth`; add `PyJWT` dependency; extend `.env.example` with Supabase vars; docs pointer.
2. **Prisma model** — `StaffRole` enum + `Staff` model (unique `supabaseAuthId`, email, name, role, optional `businessConfigId`); hand-written migration SQL (no local DB); regenerate client.
3. **JWT authentication** — `api/shared/infrastructure/auth/`: settings holder + `SupabaseJWTAuthentication` (HS256, aud/exp/iss claims) + unit tests with signed test tokens.
4. **Staff hexagonal module** — domain `StaffUser` + errors; driver/driven ports; `get_staff_by_supabase_auth_id` use case; Prisma adapter with mappers; container; `GET /api/staff/me/` REST + tests.
5. **API protection** — enable global DRF auth + `IsStaffMember`; `AllowAny` on public views; update affected view tests; import-linter green.
6. **Panel login** — login/logout views (GoTrue REST), `LoginRequiredMiddleware`, header with user/role, HTTP client forwards session token, panel tests.
7. **create_staff command + bootstrap docs** — management command via Supabase admin API; README/architecture docs for creating the Supabase project, users, and env setup.
8. **Closure** — full test suite, import-linter, docs review, one conventional commit per unit.

## Status

Open. Branch: `feat/supabase-auth` (to be created).