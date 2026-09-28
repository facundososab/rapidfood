"""MercadoPagoCredentialMapper — Prisma record <-> domain entity translation.

All row/domain mapping lives here (never in the repository or the use case), and
the tokens are encrypted on write and decrypted on read so the domain never
deals with ciphertext. Prisma field names are camelCase (``@map`` only renames
database columns).
"""

from __future__ import annotations

from modules.mercadopago.domain.models.mercadopago_credential import (
    MercadoPagoCredential,
)
from modules.mercadopago.infrastructure.adapters.driven.mercadopago.mercadopago_crypto import (
    MercadoPagoTokenCipher,
)


class MercadoPagoCredentialMapper:
    def __init__(self, cipher: MercadoPagoTokenCipher) -> None:
        self._cipher = cipher

    def to_domain(self, record: object) -> MercadoPagoCredential:
        refresh_token = record.refreshToken  # type: ignore[attr-defined]
        return MercadoPagoCredential(
            credential_id=str(record.id),  # type: ignore[attr-defined]
            business_config_id=str(record.businessConfigId),  # type: ignore[attr-defined]
            access_token=self._cipher.decrypt(record.accessToken),  # type: ignore[attr-defined]
            refresh_token=(
                self._cipher.decrypt(refresh_token) if refresh_token else None
            ),
            user_id=record.userId,  # type: ignore[attr-defined]
            public_key=record.publicKey,  # type: ignore[attr-defined]
            live_mode=bool(record.liveMode),  # type: ignore[attr-defined]
            created_at=getattr(record, "createdAt", None),
            updated_at=getattr(record, "updatedAt", None),
        )

    def to_data(self, credential: MercadoPagoCredential) -> dict[str, object]:
        """Map the domain entity to the Prisma column payload (tokens encrypted)."""
        return {
            "accessToken": self._cipher.encrypt(credential.access_token),
            "refreshToken": (
                self._cipher.encrypt(credential.refresh_token)
                if credential.refresh_token
                else None
            ),
            "userId": credential.user_id,
            "publicKey": credential.public_key,
            "liveMode": credential.live_mode,
        }
