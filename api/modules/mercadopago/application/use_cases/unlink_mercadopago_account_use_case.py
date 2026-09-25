"""Unlink the Mercado Pago account of a business.

Unlinking must be idempotent: the panel may call it twice, and a business that
never connected must not surface an error.
"""

from modules.mercadopago.application.ports.driven.mercadopago_credential_repository import (
    MercadoPagoCredentialRepositoryPort,
)
from modules.mercadopago.application.ports.driver.unlink_mercadopago_account_port import (
    UnlinkMercadoPagoAccountCommand,
)


class UnlinkMercadoPagoAccountUseCase:
    def __init__(self, repository: MercadoPagoCredentialRepositoryPort) -> None:
        self._repository = repository

    def execute(self, command: UnlinkMercadoPagoAccountCommand) -> None:
        self._repository.delete(command.business_config_id)
