"""DRF JWT authentication for Supabase Auth (GoTrue) access tokens.

Validates ``Authorization: Bearer <token>`` against the project JWT secret
(HS256, default Supabase signing). Claims checked: ``aud`` (authenticated),
``iss`` (project auth endpoint) and ``exp``.

The authenticated principal is the Supabase identity (``sub`` claim). Resolving
the restaurant staff row and applying role-based authorization is a separate
concern (permission layer), not part of this class.
"""

import logging
from dataclasses import dataclass
from typing import Optional

import jwt
from rest_framework import authentication
from rest_framework.exceptions import AuthenticationFailed

from shared.infrastructure.auth.settings import SupabaseAuthSettings

logger = logging.getLogger(__name__)

DEFAULT_ISSUER_PATH = "/auth/v1"


@dataclass(frozen=True)
class SupabasePrincipal:
    """Authenticated Supabase identity (no staff/domain resolution here)."""

    id: str
    email: Optional[str] = None
    is_authenticated: bool = True
    is_anonymous: bool = False


class SupabaseJWTAuthentication(authentication.BaseAuthentication):
    def __init__(self, settings: Optional[SupabaseAuthSettings] = None) -> None:
        self.settings = settings or SupabaseAuthSettings.from_env()

    def authenticate(self, request):
        header = authentication.get_authorization_header(request)
        if not header:
            return None  # anonymous

        try:
            auth_parts = header.decode("utf-8").split()
        except UnicodeDecodeError:
            raise AuthenticationFailed("Invalid Authorization header encoding.")

        if len(auth_parts) != 2 or auth_parts[0].lower() != "bearer":
            raise AuthenticationFailed(
                "Authorization header must be `Bearer <token>`."
            )

        token = auth_parts[1]
        payload = self._verify_token(token)
        principal = SupabasePrincipal(
            id=payload["sub"],
            email=payload.get("email"),
        )
        return (principal, token)

    def _verify_token(self, token: str) -> dict:
        secret = self.settings.jwt_secret
        if not secret:
            raise AuthenticationFailed(
                "Supabase Auth is not configured (SUPABASE_JWT_SECRET missing)."
            )

        options = {
            "require": ["exp"],
        }
        verify = {"aud": "authenticated"}

        issuer = (
            f"{self.settings.url.rstrip('/')}{DEFAULT_ISSUER_PATH}"
            if self.settings.url
            else None
        )
        if issuer:
            verify["iss"] = issuer

        try:
            return jwt.decode(
                token,
                secret,
                algorithms=["HS256"],
                audience=verify["aud"],
                issuer=verify.get("iss"),
                options=options,
            )
        except jwt.ExpiredSignatureError as exc:
            raise AuthenticationFailed("Token expired.") from exc
        except jwt.InvalidAudienceError as exc:
            raise AuthenticationFailed("Token audience is not `authenticated`.") from exc
        except jwt.InvalidIssuerError as exc:
            raise AuthenticationFailed("Token issuer does not match Supabase project.") from exc
        except jwt.PyJWTError as exc:
            raise AuthenticationFailed(f"Invalid token: {exc}") from exc