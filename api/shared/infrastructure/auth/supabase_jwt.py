"""DRF JWT authentication for Supabase Auth (GoTrue) access tokens.

Two verification modes, chosen by configuration:

- **JWKS mode** (default for new Supabase projects): the project signs tokens
  with ES256/RS256 and publishes the public keys at
  ``<SUPABASE_URL>/auth/v1/.well-known/jwks.json``. The ``kid`` in the token
  header selects the key. No secret needed.
- **HS256 legacy mode**: older projects sign with the project JWT secret
  (``SUPABASE_JWT_SECRET``). Used only when that setting is present.

Claims checked in both modes: ``aud`` (authenticated), ``iss`` (the project
auth endpoint) and ``exp``.

The authenticated principal is the Supabase identity (``sub`` claim). Resolving
the restaurant staff row and applying role-based authorization is a separate
concern (permission layer), not part of this class.
"""

import base64
import logging
import time
from dataclasses import dataclass
from typing import Optional

import jwt
import requests
from rest_framework import authentication
from rest_framework.exceptions import AuthenticationFailed

from shared.infrastructure.auth.settings import SupabaseAuthSettings

logger = logging.getLogger(__name__)

DEFAULT_ISSUER_PATH = "/auth/v1"
JWKS_PATH = "/auth/v1/.well-known/jwks.json"
JWKS_CACHE_TTL_SECONDS = 3600

_jwks_cache: dict = {"ts": 0.0, "data": None}


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

    # -- verification ------------------------------------------------------

    def _verify_token(self, token: str) -> dict:
        options = {"require": ["exp"]}
        issuer = (
            f"{self.settings.url.rstrip('/')}{DEFAULT_ISSUER_PATH}"
            if self.settings.url
            else None
        )
        verify_kwargs: dict = {
            "audience": "authenticated",
            "options": options,
        }
        if issuer:
            verify_kwargs["issuer"] = issuer

        algorithm = _unverified_header(token).get("alg")
        if algorithm == "HS256":
            return self._decode_hs256(token, verify_kwargs)
        return self._decode_jwks(token, verify_kwargs)

    def _decode_hs256(self, token: str, verify_kwargs: dict) -> dict:
        if not self.settings.jwt_secret:
            raise AuthenticationFailed(
                "Token is HS256 but SUPABASE_JWT_SECRET is not configured."
            )
        try:
            return jwt.decode(
                token,
                self.settings.jwt_secret,
                algorithms=["HS256"],
                **verify_kwargs,
            )
        except jwt.ExpiredSignatureError as exc:
            raise AuthenticationFailed("Token expired.") from exc
        except jwt.InvalidAudienceError as exc:
            raise AuthenticationFailed("Token audience is not `authenticated`.") from exc
        except jwt.InvalidIssuerError as exc:
            raise AuthenticationFailed("Token issuer does not match Supabase project.") from exc
        except jwt.PyJWTError as exc:
            raise AuthenticationFailed(f"Invalid token: {exc}") from exc

    def _decode_jwks(self, token: str, verify_kwargs: dict) -> dict:
        jwks = self._resolve_jwks()
        header = _unverified_header(token)
        keys = jwks.get("keys", [])
        key = next((k for k in keys if k.get("kid") == header.get("kid")), None)
        if key is None and len(keys) == 1 and not keys[0].get("kid"):
            key = keys[0]  # single unkeyed JWK: accept without kid match
        if key is None:
            raise AuthenticationFailed("No matching JWKS key for token kid.")

        algorithm = key.get("alg")
        if not algorithm:
            raise AuthenticationFailed("JWKS key is missing the `alg` field.")
        public_key = _public_key_from_jwk(key)
        try:
            return jwt.decode(
                token,
                public_key,
                algorithms=[algorithm],
                **verify_kwargs,
            )
        except jwt.ExpiredSignatureError as exc:
            raise AuthenticationFailed("Token expired.") from exc
        except jwt.InvalidAudienceError as exc:
            raise AuthenticationFailed("Token audience is not `authenticated`.") from exc
        except jwt.InvalidIssuerError as exc:
            raise AuthenticationFailed("Token issuer does not match Supabase project.") from exc
        except jwt.PyJWTError as exc:
            raise AuthenticationFailed(f"Invalid token: {exc}") from exc

    # -- JWKS helpers -------------------------------------------------------

    def _jwks_url(self) -> str:
        if not self.settings.url:
            raise AuthenticationFailed(
                "Supabase Auth is not configured (SUPABASE_URL missing and "
                "no SUPABASE_JWT_SECRET set)."
            )
        return f"{self.settings.url.rstrip('/')}{JWKS_PATH}"

    def _resolve_jwks(self) -> dict:
        now = time.monotonic()
        cached = _jwks_cache["data"]
        if cached is not None and (now - _jwks_cache["ts"]) < JWKS_CACHE_TTL_SECONDS:
            return cached

        url = self._jwks_url()
        try:
            response = requests.get(url, timeout=10)
            response.raise_for_status()
            data = response.json()
        except requests.RequestException as exc:
            raise AuthenticationFailed(
                f"Could not fetch Supabase JWKS from {url}: {exc}"
            ) from exc

        if not isinstance(data, dict) or "keys" not in data:
            raise AuthenticationFailed("Supabase JWKS response has no keys.")
        _jwks_cache["ts"] = now
        _jwks_cache["data"] = data
        return data


def _unverified_header(token: str) -> dict:
    try:
        return jwt.get_unverified_header(token)
    except jwt.PyJWTError as exc:
        raise AuthenticationFailed(f"Malformed token header: {exc}") from exc


def _b64url_int(value: str) -> int:
    padding = "=" * (-len(value) % 4)
    return int.from_bytes(base64.urlsafe_b64decode(value + padding), "big")


def _public_key_from_jwk(jwk: dict):
    """Build a cryptography public key object from a JWK (EC or RSA)."""
    from cryptography.hazmat.primitives.asymmetric import ec, rsa
    from cryptography.hazmat.primitives.asymmetric.rsa import RSAPublicNumbers

    kty = jwk.get("kty")
    if kty == "EC":
        curve = _ec_curve(jwk.get("crv"))
        public_numbers = ec.EllipticCurvePublicNumbers(
            _b64url_int(jwk["x"]),
            _b64url_int(jwk["y"]),
            curve,
        )
        return public_numbers.public_key()
    if kty == "RSA":
        return RSAPublicNumbers(
            _b64url_int(jwk["e"]),
            _b64url_int(jwk["n"]),
        ).public_key()
    raise AuthenticationFailed(f"Unsupported JWK key type: {kty}")


def _ec_curve(crv: Optional[str]):
    from cryptography.hazmat.primitives.asymmetric import ec

    return {
        "P-256": ec.SECP256R1(),
        "P-384": ec.SECP384R1(),
        "P-521": ec.SECP521R1(),
    }.get(crv) or ec.SECP256R1()