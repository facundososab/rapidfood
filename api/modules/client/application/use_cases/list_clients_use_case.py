from modules.client.application.ports.driver.list_clients_ports import (
    ListClientsPort,
    ListClientsQuery,
)
from modules.client.application.ports.driven.client_repository_port import (
    ClientRepositoryPort,
)
from modules.client.domain.models.client import Client


class ListClientsUseCase(ListClientsPort):
    def __init__(self, clients: ClientRepositoryPort) -> None:
        self._clients = clients

    def execute(self, query: ListClientsQuery) -> list[Client]:
        return self._clients.list(search=query.search)