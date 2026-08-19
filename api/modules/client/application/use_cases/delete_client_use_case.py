from modules.client.application.ports.driver.delete_client_ports import (
    DeleteClientCommand,
    DeleteClientPort,
    DeleteClientResponse,
)
from modules.client.application.ports.driven.client_repository_port import (
    ClientRepositoryPort,
)
from modules.client.domain.errors.client_errors import ClientNotFoundError


class DeleteClientUseCase(DeleteClientPort):
    def __init__(self, clients: ClientRepositoryPort) -> None:
        self._clients = clients

    def execute(self, command: DeleteClientCommand) -> DeleteClientResponse:
        if not self._clients.client_exists(command.client_id):
            raise ClientNotFoundError(command.client_id)

        self._clients.delete(command.client_id)

        return DeleteClientResponse(id=command.client_id)