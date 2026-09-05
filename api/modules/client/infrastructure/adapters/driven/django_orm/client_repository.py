from modules.client.application.ports.driven.client_repository_port import (
    ClientRepositoryPort,
)
from modules.client.domain.models.client import Client
from modules.client.infrastructure.adapters.driven.django_orm.models import (
    ClientModel,
)
from django.db.models import Q


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

    def list(self, search: str | None = None) -> list[Client]:
        queryset = ClientModel.objects.all()
        if search:
            needle = search.strip()
            queryset = queryset.filter(
                Q(name__icontains=needle)
                | Q(last_name__icontains=needle)
                | Q(phone_number__icontains=needle)
            )
        return [self._to_domain(model) for model in queryset]

    def delete(self, client_id: str) -> None:
        ClientModel.objects.filter(id=client_id).delete()

    def client_exists(self, client_id: str) -> bool:
        return ClientModel.objects.filter(id=client_id).exists()

    @staticmethod
    def _to_domain(model: ClientModel) -> Client:
        return Client(
            id=model.id,
            name=model.name,
            lastName=model.last_name,
            phoneNumber=model.phone_number,
        )
