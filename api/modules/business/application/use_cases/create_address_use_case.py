from __future__ import annotations

from modules.business.application.ports.driven.business_repository_port import (
    BusinessConfigurationRepositoryPort,
)
from modules.business.application.ports.driver.create_address_port import (
    CreateAddressCommand,
)
from modules.business.domain.errors.business_errors import (
    BusinessConfigurationNotFoundError,
)


class CreateAddressUseCase:
    def __init__(self, repo: BusinessConfigurationRepositoryPort) -> None:
        self._repo = repo

    def execute(self, command: CreateAddressCommand) -> dict:
        # Ensure business exists
        config = self._repo.get_by_id(command.business_config_id)
        if config is None:
            raise BusinessConfigurationNotFoundError(command.business_config_id)
        address = self._repo.create_address(
            command.business_config_id,
            street=command.street,
            street_number=command.street_number,
            city=command.city,
            province=command.province,
            floor=command.floor,
            apartment=command.apartment,
            postal_code=command.postal_code,
        )
        return {
            "id": address.id,
            "street": address.street,
            "streetNumber": address.streetNumber,
            "city": address.city,
            "province": address.province,
            "floor": address.floor,
            "apartment": address.apartment,
            "postalCode": address.postalCode,
            "label": address.full_label(),
        }
