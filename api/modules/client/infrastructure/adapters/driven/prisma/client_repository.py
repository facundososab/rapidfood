from prisma.types import ClientWhereInput
from modules.client.application.ports.driven.client_repository_port import (
    ClientRepositoryPort,
)
from modules.client.domain.models.client import Client
from shared.infrastructure.prisma.db import db


class PrismaClientRepository(ClientRepositoryPort):
    def save(self, client: Client) -> None:
        db.client.client.upsert(
            where={"id": client.id},
            data={
                "create": {
                    "id": client.id,
                    "name": client.name,
                    "lastName": client.last_name,
                    "phoneNumber": client.phone_number,
                },
                "update": {
                    "name": client.name,
                    "lastName": client.last_name,
                    "phoneNumber": client.phone_number,
                },
            },
        )

    def find_by_id(self, client_id: str) -> Client | None:
        record = db.client.client.find_unique(where={"id": client_id})
        return self._to_domain(record) if record is not None else None

    def find_by_phone(self, phone_number: str) -> Client | None:
        record = db.client.client.find_first(where={"phoneNumber": phone_number})
        return self._to_domain(record) if record is not None else None

    def update(self, client: Client) -> None:
        db.client.client.update(
            where={"id": client.id},
            data={
                "name": client.name,
                "lastName": client.last_name,
                "phoneNumber": client.phone_number,
            },
        )

    def list(self, search: str | None = None) -> list[Client]:
        where: ClientWhereInput | None = None
        if search:
            needle = search.strip()
            where = {
                "OR": [
                    {"name": {"contains": needle}},
                    {"lastName": {"contains": needle}},
                    {"phoneNumber": {"contains": needle}},
                ]
            }
        records = db.client.client.find_many(where=where)
        return [self._to_domain(record) for record in records]

    def delete(self, client_id: str) -> None:
        db.client.client.delete(where={"id": client_id})

    def client_exists(self, client_id: str) -> bool:
        return db.client.client.find_unique(where={"id": client_id}) is not None

    @staticmethod
    def _to_domain(record) -> Client:
        return Client(
            id=record.id,
            name=record.name,
            last_name=record.lastName,
            phone_number=record.phoneNumber,
        )