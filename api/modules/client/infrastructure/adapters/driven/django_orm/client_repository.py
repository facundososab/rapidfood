from modules.client.application.ports.driven.client_repository_port import (
    ClientRepositoryPort,
)
from modules.client.domain.models.client import Client
from modules.client.infrastructure.adapters.driven.django_orm.models import (
    ClientModel,
)


class DjangoClientRepository(ClientRepositoryPort):
    def save(self, client: Client) -> None:
        ClientModel.objects.update_or_create(
            id=client.id,
            defaults={
                "name": client.name,
                "last_name": client.last_name,
                "phone_number": client.phone_number,
            },
        )

    def find_by_id(self, client_id: str) -> Client | None:
        model = ClientModel.objects.filter(id=client_id).first()
        if model is None:
            return None
        return self._to_domain(model)

    def find_by_phone(self, phone_number: str) -> Client | None:
        model = ClientModel.objects.filter(phone_number=phone_number).first()
        if model is None:
            return None
        return self._to_domain(model)

    def update(self, client: Client) -> None:
        ClientModel.objects.filter(id=client.id).update(
            name=client.name,
            last_name=client.last_name,
            phone_number=client.phone_number,
        )

    @staticmethod
    def _to_domain(model: ClientModel) -> Client:
        return Client(
            id=model.id,
            name=model.name,
            last_name=model.last_name,
            phone_number=model.phone_number,
        )
