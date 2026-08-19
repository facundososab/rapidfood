from modules.client.application.ports.driver.get_client_ports import (
    GetClientPort,
    GetClientQuery,
)
from modules.client.application.ports.driven.client_repository_port import (
    ClientRepositoryPort,
)
from modules.client.domain.errors.client_errors import ClientNotFoundError
from modules.client.domain.models.client import Client


class GetClientUseCase(GetClientPort):
    def __init__(self, clients: ClientRepositoryPort) -> None:
        self._clients = clients

    def execute(self, query: GetClientQuery) -> Client:
        client = self._clients.find_by_id(query.client_id)
        if client is None:
            raise ClientNotFoundError(query.client_id)
        return client