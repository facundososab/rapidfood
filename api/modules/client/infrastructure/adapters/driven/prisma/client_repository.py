from modules.client.application.ports.driven.client_repository_port import (
    ClientRepositoryPort,
)
from modules.client.domain.models.client import Client
from shared.infrastructure.prisma.db import db


class PrismaClientRepository(ClientRepositoryPort):
    def find_by_id(self, client_id: str) -> Client | None:
        record = db.client.client.find_unique(where={"id": client_id})
        return self._to_domain(record) if record is not None else None

    def list(self, search: str | None = None) -> list[Client]:
        where: dict = {}
        if search:
            needle = search.strip()
            where["OR"] = [
                {"name": {"contains": needle}},
                {"lastName": {"contains": needle}},
                {"phoneNumber": {"contains": needle}},
            ]
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
            lastName=record.lastName,
            phoneNumber=record.phoneNumber,
        )