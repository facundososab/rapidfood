"""Supabase Auth integration (cross-cutting infrastructure).

Identity provider only: GoTrue issues JWTs (email+password). This package owns
JWT verification for the DRF shell; staff roles/authorization live in the
Prisma-owned database (modules.staff), never in token claims.
"""

__all__ = [
    "SupabaseAuthSettings",
    "SupabasePrincipal",
    "SupabaseJWTAuthentication",
]