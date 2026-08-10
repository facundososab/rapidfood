import uuid
from modules.client.application.use_cases.create_client_use_case import CreateClientUseCase
from modules.client.application.use_cases.update_client_use_case import UpdateClientUseCase
from modules.client.application.use_cases.add_address_use_case import AddAddressUseCase
from modules.client.application.use_cases.update_address_use_case import UpdateAddressUseCase
from modules.client.application.use_cases.remove_address_use_case import RemoveAddressUseCase
from modules.client.application.use_cases.set_default_address_use_case import SetDefaultAddressUseCase
from modules.client.infrastructure.adapters.driven.django_orm.client_repository import DjangoClientRepository
from modules.client.infrastructure.adapters.driven.django_orm.address_repository import DjangoAddressRepository
from modules.client.infrastructure.adapters.driven.django_orm.client_query_adapter import DjangoClientQueryAdapter


class UuidIdGenerator:
    def generate(self) -> str:
        return str(uuid.uuid4())


class ClientContainer:
    _client_repository = DjangoClientRepository()
    _address_repository = DjangoAddressRepository()
    _id_generator = UuidIdGenerator()
    _client_query_adapter = DjangoClientQueryAdapter()

    @classmethod
    def create_client_use_case(cls) -> CreateClientUseCase:
        return CreateClientUseCase(cls._client_repository, cls._id_generator)

    @classmethod
    def update_client_use_case(cls) -> UpdateClientUseCase:
        return UpdateClientUseCase(cls._client_repository)

    @classmethod
    def add_address_use_case(cls) -> AddAddressUseCase:
        return AddAddressUseCase(cls._client_repository, cls._address_repository, cls._id_generator)
        
    @classmethod
    def update_address_use_case(cls) -> UpdateAddressUseCase:
        return UpdateAddressUseCase(cls._address_repository)
        
    @classmethod
    def remove_address_use_case(cls) -> RemoveAddressUseCase:
        return RemoveAddressUseCase(cls._address_repository)
        
    @classmethod
    def set_default_address_use_case(cls) -> SetDefaultAddressUseCase:
        return SetDefaultAddressUseCase(cls._address_repository)
        
    @classmethod
    def client_query_adapter(cls) -> DjangoClientQueryAdapter:
        return cls._client_query_adapter
