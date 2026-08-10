from modules.client.application.ports.driver.address_ports import (
    SetDefaultAddressCommand,
    SetDefaultAddressPort,
    AddressResponse,
)
from modules.client.application.ports.driven.address_repository_port import (
    AddressRepositoryPort,
)
from modules.client.domain.errors.client_errors import (
    AddressNotFoundError,
    AddressNotOwnedByClientError,
)


class SetDefaultAddressUseCase(SetDefaultAddressPort):
    def __init__(
        self,
        address_repository: AddressRepositoryPort,
    ) -> None:
        self._address_repository = address_repository

    def execute(self, command: SetDefaultAddressCommand) -> AddressResponse:
        address = self._address_repository.find_by_id(command.address_id)
        if address is None:
            raise AddressNotFoundError(command.address_id)

        if address.client_id != command.client_id:
            raise AddressNotOwnedByClientError(
                f"Address '{command.address_id}' is not owned by client '{command.client_id}'"
            )

        self._address_repository.unset_default_for_client(command.client_id)
        address.mark_as_default()
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
