"""Mercado Pago credential — the OAuth link between a business and an MP account.

OAuth tokens are stored encrypted at rest (the persistence adapter owns the
cipher); at the domain level they are plain strings that the link use case
receives from Mercado Pago and hands to the repository.

The entity protects the invariants that make a credential usable: it must be
bound to a business configuration and it must carry an access token.
"""

from dataclasses import dataclass
from datetime import datetime


@dataclass
class MercadoPagoCredential:
    business_config_id: str
    access_token: str
    refresh_token: str | None = None
    user_id: str | None = None
    public_key: str | None = None
    live_mode: bool = False
    credential_id: str | None = None
    created_at: datetime | None = None
    updated_at: datetime | None = None

    def __post_init__(self) -> None:
        if not self.business_config_id or not self.business_config_id.strip():
            raise ValueError("business_config_id cannot be blank")
        if not self.access_token or not self.access_token.strip():
            raise ValueError("access_token cannot be blank")

    @classmethod
    def create(
        cls,
        business_config_id: str,
        access_token: str,
        refresh_token: str | None = None,
        user_id: str | None = None,
        public_key: str | None = None,
        live_mode: bool = False,
        credential_id: str | None = None,
    ) -> "MercadoPagoCredential":
        return cls(
            business_config_id=business_config_id.strip(),
            access_token=access_token,
            refresh_token=refresh_token,
            user_id=user_id,
            public_key=public_key,
            live_mode=live_mode,
            credential_id=credential_id,
        )

    @property
    def is_linked(self) -> bool:
        return bool(self.access_token.strip())
