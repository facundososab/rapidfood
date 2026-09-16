from modules.client.application.ports.driver.add_address_ports import (
    AddAddressCommand,
    AddAddressPort,
    AddressResponse,
)
from modules.client.application.ports.driven.client_repository_port import (
    ClientRepositoryPort,
)
from modules.client.application.ports.driven.address_repository_port import (
    AddressRepositoryPort,
)
from modules.client.application.ports.driven.id_generator_port import (
    IdGeneratorPort,
)
from modules.client.domain.errors.client_errors import ClientNotFoundError
from modules.client.domain.models.address import Address


class AddAddressUseCase(AddAddressPort):
    def __init__(
        self,
        client_repository: ClientRepositoryPort,
        address_repository: AddressRepositoryPort,
        id_generator: IdGeneratorPort,
    ) -> None:
        self._client_repository = client_repository
        self._address_repository = address_repository
        self._id_generator = id_generator

    def execute(self, command: AddAddressCommand) -> AddressResponse:
        client = self._client_repository.find_by_id(command.client_id)
        if client is None:
            raise ClientNotFoundError(command.client_id)

        if command.is_default:
            self._address_repository.unset_default_for_client(command.client_id)

        address = Address.create(
            address_id=self._id_generator.generate(),
            client_id=command.client_id,
            street=command.street,
            street_number=command.street_number,
            city=command.city,
            province=command.province,
            latitude=command.latitude,
            longitude=command.longitude,
            floor=command.floor,
            apartment=command.apartment,
            postal_code=command.postal_code,
            delivery_instructions=command.delivery_instructions,
            label=command.label,
            is_default=command.is_default,
        )
        self._address_repository.save(address)

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
