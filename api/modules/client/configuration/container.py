from modules.client.application.use_cases.delete_client_use_case import (
    DeleteClientUseCase,
)
from modules.client.application.use_cases.get_client_use_case import GetClientUseCase
from modules.client.application.use_cases.list_clients_use_case import ListClientsUseCase
from modules.client.infrastructure.adapters.driven.prisma.client_repository import (
    PrismaClientRepository,
)


class ClientContainer:
    def __init__(self) -> None:
        clients = PrismaClientRepository()

        self.delete_client = DeleteClientUseCase(clients)
        self.get_client = GetClientUseCase(clients)
        self.list_clients = ListClientsUseCase(clients)


def get_client_container() -> ClientContainer:
    return ClientContainer()