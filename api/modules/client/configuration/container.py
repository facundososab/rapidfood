import uuid

from modules.client.application.use_cases.add_address_use_case import AddAddressUseCase
from modules.client.application.use_cases.create_client_use_case import CreateClientUseCase
from modules.client.application.use_cases.delete_client_use_case import DeleteClientUseCase
from modules.client.application.use_cases.get_client_use_case import GetClientUseCase
from modules.client.application.use_cases.list_clients_use_case import ListClientsUseCase
from modules.client.application.use_cases.remove_address_use_case import RemoveAddressUseCase
from modules.client.application.use_cases.set_default_address_use_case import (
    SetDefaultAddressUseCase,
)
from modules.client.application.use_cases.update_address_use_case import UpdateAddressUseCase
from modules.client.application.use_cases.update_client_use_case import UpdateClientUseCase
from modules.client.infrastructure.adapters.driven.prisma.address_repository import (
    PrismaAddressRepository,
)
from modules.client.infrastructure.adapters.driven.prisma.client_query_adapter import (
    PrismaClientQueryAdapter,
)
from modules.client.infrastructure.adapters.driven.prisma.client_repository import (
    PrismaClientRepository,
)


class UuidIdGenerator:
    def generate(self) -> str:
        return str(uuid.uuid4())


class ClientContainer:
    def __init__(self) -> None:
        client_repository = PrismaClientRepository()
        address_repository = PrismaAddressRepository()
        id_generator = UuidIdGenerator()

        self.create_client = CreateClientUseCase(client_repository, id_generator)
        self.update_client = UpdateClientUseCase(client_repository)
        self.add_address = AddAddressUseCase(client_repository, address_repository, id_generator)
        self.update_address = UpdateAddressUseCase(address_repository)
        self.remove_address = RemoveAddressUseCase(address_repository)
        self.set_default_address = SetDefaultAddressUseCase(address_repository)
        self.get_client = GetClientUseCase(client_repository)
        self.list_clients = ListClientsUseCase(client_repository)
        self.delete_client = DeleteClientUseCase(client_repository)
        self.client_query_adapter = PrismaClientQueryAdapter()


def get_client_container() -> ClientContainer:
    return ClientContainer()
