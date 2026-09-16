from modules.client.application.ports.driver.remove_address_ports import (
    RemoveAddressCommand,
    RemoveAddressPort,
)
from modules.client.application.ports.driven.address_repository_port import (
    AddressRepositoryPort,
)
from modules.client.domain.errors.client_errors import (
    AddressNotFoundError,
    AddressNotOwnedByClientError,
)


class RemoveAddressUseCase(RemoveAddressPort):
    def __init__(
        self,
        address_repository: AddressRepositoryPort,
    ) -> None:
        self._address_repository = address_repository

    def execute(self, command: RemoveAddressCommand) -> None:
        address = self._address_repository.find_by_id(command.address_id)
        if address is None:
            raise AddressNotFoundError(command.address_id)

        if address.client_id != command.client_id:
            raise AddressNotOwnedByClientError(
                f"Address '{command.address_id}' is not owned by client '{command.client_id}'"
            )

        self._address_repository.delete(command.address_id)
