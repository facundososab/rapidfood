from modules.client.application.ports.driver.add_address_ports import (
    AddressResponse,
)
from modules.client.application.ports.driver.update_address_ports import (
    UpdateAddressCommand,
    UpdateAddressPort,
)
from modules.client.application.ports.driven.address_repository_port import (
    AddressRepositoryPort,
)
from modules.client.domain.errors.client_errors import (
    AddressNotFoundError,
    AddressNotOwnedByClientError,
)


class UpdateAddressUseCase(UpdateAddressPort):
    def __init__(
        self,
        address_repository: AddressRepositoryPort,
    ) -> None:
        self._address_repository = address_repository

    def execute(self, command: UpdateAddressCommand) -> AddressResponse:
        address = self._address_repository.find_by_id(command.address_id)
        if address is None:
            raise AddressNotFoundError(command.address_id)

        if address.client_id != command.client_id:
            raise AddressNotOwnedByClientError(
                f"Address '{command.address_id}' is not owned by client '{command.client_id}'"
            )

        address.update(
            street=command.street,
            street_number=command.street_number,
            city=command.city,
            province=command.province,
            latitude=command.latitude,
            longitude=command.longitude,
            floor=command.floor,
            apartment=command.apartment,
            postal_code=command.postal_code,
            delivery_instructions=command.delivery_instructions,
            label=command.label,
        )
        self._address_repository.update(address)

        return AddressResponse(
            id=address.id,
            client_id=address.client_id,
            street=address.street,
            street_number=address.street_number,
            city=address.city,
            province=address.province,
            latitude=address.latitude,
            longitude=address.longitude,
            floor=address.floor,
            apartment=address.apartment,
            postal_code=address.postal_code,
            delivery_instructions=address.delivery_instructions,
            label=address.label,
            is_default=address.is_default,
        )
