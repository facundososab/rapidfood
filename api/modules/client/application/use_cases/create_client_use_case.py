from modules.client.application.ports.driver.create_client_ports import (
    CreateClientCommand,
    CreateClientPort,
    ClientResponse,
)
from modules.client.application.ports.driven.client_repository_port import (
    ClientRepositoryPort,
)
from modules.client.application.ports.driven.id_generator_port import (
    IdGeneratorPort,
)
from modules.client.domain.errors.client_errors import ClientAlreadyExistsError
from modules.client.domain.models.client import Client


class CreateClientUseCase(CreateClientPort):
    def __init__(
        self,
        client_repository: ClientRepositoryPort,
        id_generator: IdGeneratorPort,
    ) -> None:
        self._client_repository = client_repository
        self._id_generator = id_generator

    def execute(self, command: CreateClientCommand) -> ClientResponse:
        existing = self._client_repository.find_by_phone(command.phone_number)
        if existing is not None:
            raise ClientAlreadyExistsError(command.phone_number)

        client = Client.create(
            client_id=self._id_generator.generate(),
            name=command.name,
            last_name=command.last_name,
            phone_number=command.phone_number,
        )
        self._client_repository.save(client)

        return ClientResponse(
            id=client.id,
            name=client.name,
            last_name=client.last_name,
            phone_number=client.phone_number,
        )
