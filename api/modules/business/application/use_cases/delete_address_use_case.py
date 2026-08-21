from __future__ import annotations

from modules.business.application.ports.driven.business_repository_port import (
    BusinessConfigurationRepositoryPort,
)
from modules.business.application.ports.driver.delete_address_port import (
    DeleteAddressCommand,
)
from modules.business.domain.errors.business_errors import (
    AddressDoesNotBelongToBusinessError,
    AddressNotFoundError,
)


class DeleteAddressUseCase:
    def __init__(self, repo: BusinessConfigurationRepositoryPort) -> None:
        self._repo = repo

    def execute(self, command: DeleteAddressCommand) -> None:
        address = self._repo.get_address_by_id(command.address_id)
        if address is None:
            raise AddressNotFoundError(command.address_id)
        if address.businessConfigId != command.business_config_id:
            raise AddressDoesNotBelongToBusinessError(
                command.address_id, command.business_config_id
            )
        self._repo.delete_address(command.address_id)
