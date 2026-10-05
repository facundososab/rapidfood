"""Read the access token linked by a business, without deciding how to charge.

An unlinked business is a normal state, not an error: the caller (for example
the order payment flow) owns the fallback to the globally configured token.
"""

from modules.mercadopago.application.ports.driven.mercadopago_credential_repository import (
    MercadoPagoCredentialRepositoryPort,
)
from modules.mercadopago.application.ports.driver.get_mercadopago_access_token_port import (
    GetMercadoPagoAccessTokenQuery,
)


class GetMercadoPagoAccessTokenUseCase:
    def __init__(self, repository: MercadoPagoCredentialRepositoryPort) -> None:
        self._repository = repository

    def execute(self, query: GetMercadoPagoAccessTokenQuery) -> str | None:
        credential = self._repository.get_by_business(query.business_config_id)
        if credential is None:
            return None
        return credential.access_token
