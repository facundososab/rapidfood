"""Read the Mercado Pago linkage status of a business (token-free)."""

from modules.mercadopago.application.ports.driven.mercadopago_credential_repository import (
    MercadoPagoCredentialRepositoryPort,
)
from modules.mercadopago.application.ports.driver.get_link_status_port import (
    GetLinkStatusQuery,
    GetLinkStatusResult,
)


class GetLinkStatusUseCase:
    def __init__(self, repository: MercadoPagoCredentialRepositoryPort) -> None:
        self._repository = repository

    def execute(self, query: GetLinkStatusQuery) -> GetLinkStatusResult:
        credential = self._repository.get_by_business(query.business_config_id)
        if credential is None:
            return GetLinkStatusResult(linked=False)
        return GetLinkStatusResult(
            linked=True,
            live_mode=credential.live_mode,
            user_id=credential.user_id,
            public_key=credential.public_key,
        )
