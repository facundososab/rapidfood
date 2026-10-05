"""PrismaMercadoPagoCredentialRepository — Prisma adapter of the credential port.

One row per business configuration (``businessConfigId`` is unique), so linking
again is an upsert that replaces the stored tokens. The repository only talks
to the mapper and Prisma; the Database holder is injected so tests can point it
at another client, and reaching ``database.client`` lazily means importing this
module never opens a connection.
"""

from __future__ import annotations

from prisma import Prisma

from modules.mercadopago.application.ports.driven.mercadopago_credential_repository import (
    MercadoPagoCredentialRepositoryPort,
)
from modules.mercadopago.domain.models.mercadopago_credential import (
    MercadoPagoCredential,
)
from modules.mercadopago.infrastructure.adapters.driven.mercadopago.mercadopago_crypto import (
    MercadoPagoTokenCipher,
)
from modules.mercadopago.infrastructure.adapters.driven.prisma.mappers.mercadopago_credential_mapper import (
    MercadoPagoCredentialMapper,
)
from shared.infrastructure.prisma.db import Database, db


class PrismaMercadoPagoCredentialRepository(MercadoPagoCredentialRepositoryPort):
    def __init__(
        self,
        database: Database = db,
        cipher: MercadoPagoTokenCipher | None = None,
    ) -> None:
        self._database = database
        self._mapper = MercadoPagoCredentialMapper(cipher or MercadoPagoTokenCipher.from_env())

    @property
    def _prisma(self) -> Prisma:
        return self._database.client

    def get_by_business(self, business_config_id: str) -> MercadoPagoCredential | None:
        record = self._prisma.mercadopagocredential.find_unique(
            where={"businessConfigId": business_config_id}
        )
        return self._mapper.to_domain(record) if record is not None else None

    def upsert(self, credential: MercadoPagoCredential) -> MercadoPagoCredential:
        data = self._mapper.to_data(credential)
        record = self._prisma.mercadopagocredential.upsert(
            where={"businessConfigId": credential.business_config_id},
            data={
                # businessConfigId is only writable on create (the update input
                # has no relation scalar), hence the split payload.
                "create": {"businessConfigId": credential.business_config_id, **data},
                "update": data,
            },
        )
        return self._mapper.to_domain(record)

    def delete(self, business_config_id: str) -> None:
        # delete_many keeps unlinking idempotent: zero rows deleted is not an error.
        self._prisma.mercadopagocredential.delete_many(
            where={"businessConfigId": business_config_id}
        )
