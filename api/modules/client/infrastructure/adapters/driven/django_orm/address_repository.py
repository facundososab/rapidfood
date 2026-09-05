from modules.client.application.ports.driven.address_repository_port import (
    AddressRepositoryPort,
)
from modules.client.domain.models.address import Address
from modules.client.infrastructure.adapters.driven.django_orm.models import (
    ClientAddressModel,
)


class DjangoAddressRepository(AddressRepositoryPort):
    def save(self, address: Address) -> None:
        ClientAddressModel.objects.update_or_create(
            id=address.id,
            defaults={
                "client_id": address.client_id,
                "street": address.street,
                "street_number": address.street_number,
                "city": address.city,
                "province": address.province,
                "latitude": address.latitude,
                "longitude": address.longitude,
                "floor": address.floor,
                "apartment": address.apartment,
                "postal_code": address.postal_code,
                "delivery_instructions": address.delivery_instructions,
                "label": address.label,
                "is_default": address.is_default,
            },
        )

    def find_by_id(self, address_id: str) -> Address | None:
        model = ClientAddressModel.objects.filter(id=address_id).first()
        if model is None:
            return None
        return self._to_domain(model)

    def find_by_client_id(self, client_id: str) -> list[Address]:
        models = ClientAddressModel.objects.filter(client_id=client_id)
        return [self._to_domain(model) for model in models]

    def update(self, address: Address) -> None:
        ClientAddressModel.objects.filter(id=address.id).update(
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

    def delete(self, address_id: str) -> None:
        ClientAddressModel.objects.filter(id=address_id).delete()

    def unset_default_for_client(self, client_id: str) -> None:
        ClientAddressModel.objects.filter(client_id=client_id, is_default=True).update(
            is_default=False
        )

    @staticmethod
    def _to_domain(model: ClientAddressModel) -> Address:
        return Address(
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
