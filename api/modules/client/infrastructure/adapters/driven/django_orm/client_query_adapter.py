from modules.client.application.ports.driver.client_query_port import (
    ClientQueryPort,
    ClientDTO,
    AddressDTO,
)
from modules.client.infrastructure.adapters.driven.django_orm.models import (
    ClientModel,
    ClientAddressModel,
)


class DjangoClientQueryAdapter(ClientQueryPort):
    def find_by_id(self, client_id: str) -> ClientDTO | None:
        model = ClientModel.objects.filter(id=client_id).first()
        if model is None:
            return None
        return ClientDTO(
            id=model.id,
            name=model.name,
            last_name=model.last_name,
            phone_number=model.phone_number,
        )

    def find_by_phone_number(self, phone: str) -> ClientDTO | None:
        model = ClientModel.objects.filter(phone_number=phone).first()
        if model is None:
            return None
        return ClientDTO(
            id=model.id,
            name=model.name,
            last_name=model.last_name,
            phone_number=model.phone_number,
        )

    def get_address(self, address_id: str) -> AddressDTO | None:
        model = ClientAddressModel.objects.filter(id=address_id).first()
        if model is None:
            return None
        return AddressDTO(
            id=model.id,
            client_id=model.client_id,
            street=model.street,
            street_number=model.street_number,
            city=model.city,
            province=model.province,
            latitude=model.latitude,
            longitude=model.longitude,
            floor=model.floor,
            apartment=model.apartment,
            postal_code=model.postal_code,
            delivery_instructions=model.delivery_instructions,
            label=model.label,
            is_default=model.is_default,
        )
