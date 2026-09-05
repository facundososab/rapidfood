from modules.client.application.ports.driver.client_ports import (
    UpdateClientCommand,
    UpdateClientPort,
    ClientResponse,
)
from modules.client.application.ports.driven.client_repository_port import (
    ClientRepositoryPort,
)
from modules.client.domain.errors.client_errors import (
    ClientNotFoundError,
    ClientAlreadyExistsError,
)


class UpdateClientUseCase(UpdateClientPort):
    def __init__(
        self,
        client_repository: ClientRepositoryPort,
    ) -> None:
        self._client_repository = client_repository

    def execute(self, command: UpdateClientCommand) -> ClientResponse:
        client = self._client_repository.find_by_id(command.client_id)
        if client is None:
            raise ClientNotFoundError(command.client_id)

        if client.phone_number != command.phone_number:
            existing = self._client_repository.find_by_phone(command.phone_number)
            if existing is not None:
                raise ClientAlreadyExistsError(command.phone_number)

        client.update(
            name=command.name,
            last_name=command.last_name,
            phone_number=command.phone_number,
        )
        self._client_repository.update(client)

        return ClientResponse(
            id=client.id,
            name=client.name,
            last_name=client.last_name,
            phone_number=client.phone_number,
        )
