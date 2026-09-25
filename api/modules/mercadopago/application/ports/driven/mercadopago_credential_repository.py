"""Driven port: persistence of the per-business Mercado Pago credentials."""

from typing import Protocol

from modules.mercadopago.domain.models.mercadopago_credential import (
    MercadoPagoCredential,
)


class MercadoPagoCredentialRepositoryPort(Protocol):
    """One Mercado Pago account per business configuration."""

    def get_by_business(self, business_config_id: str) -> MercadoPagoCredential | None:
        """Return the linked credential of a business, or ``None`` when unlinked."""
        ...

    def upsert(self, credential: MercadoPagoCredential) -> MercadoPagoCredential:
        """Create the link or replace the stored tokens of an existing one."""
        ...

    def delete(self, business_config_id: str) -> None:
        """Remove the link. Idempotent: absent links are not an error."""
        ...
