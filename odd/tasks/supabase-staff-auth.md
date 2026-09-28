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

**Done.** Branch `feat/supabase-auth` — 9 commits (setup, prisma, auth, staff module,
API protection, panel, create_staff command, migration fixes, docs).

- Supabase project created via MCP: `rapidfood-db` (`usadpbrrhumlithcdmcf`, sa-east-1, free,
USD 0/mes). Credentials in local `.env` (gitignored — never committed).
- Local DB migrated clean (staff table applied). Full suite: 276 passed; the 7 failed +
6 errors are PRE-EXISTING on `main` (verified via stash): prisma `db` fixture not visible
outside prisma/tests (pytest-django 4.12) and conversation integration tests needing env.
- Fixed two pre-existing migration bugs that blocked any clean `migrate deploy`
(duplicated `is_active`/`min_order_amount` in coupon, duplicated variant column block).
- import-linter: 10 contracts kept, 0 broken. staff+auth: 25 tests, panel: 8 tests green.

Follow-ups (user-owned): paste `SUPABASE_SERVICE_ROLE_KEY` from the dashboard to give
staff via `create_staff` (or create users manually in Authentication → Users); panel
staff CRUD is out of scope.

## Timeline addendum (testing the login)

- Supabase project re-created as `rapidfood-db-v2` (`htegrsxmjjdfeaokpcvj`, sa-east-1) after
  troubleshooting (first project was paused, not broken — the failures were caused by
  hand-inserted auth.users rows, not by the project template).
- New Supabase projects sign access tokens with **ES256 + JWKS** (kid at
  `<url>/auth/v1/.well-known/jwks.json`), not HS256. `SupabaseJWTAuthentication` now
  selects the mode by token algorithm: HS256 → `SUPABASE_JWT_SECRET`; ES256/RS256 → JWKS.
- Seed users are created through GoTrue (signup/admin shape) with `email_confirmed_at`
  set via SQL; hand-inserting users with a partial profile breaks GoTrue login with
  "Database error querying schema" — clone the exact GoTrue row profile.
- Test credentials (dev only): admin@rapidfood.app / caja@rapidfood.app /
  cocina@rapidfood.app, password `Rapidfood123!`.
- Pre-existing infra fixes on this branch: `docker/backend/entrypoint.sh` had CRLF line
  endings (container: "exec /entrypoint.sh: no such file or directory"); fixed + added
  `.gitattributes` (`*.sh text eol=lf`). `docker-compose.yml` now forwards `SUPABASE_*`
  to backend and ui containers.