from modules.client.application.ports.driven.address_repository_port import (
    AddressRepositoryPort,
)
from modules.client.domain.models.address import Address
from shared.infrastructure.prisma.db import db


class PrismaAddressRepository(AddressRepositoryPort):
    def save(self, address: Address) -> None:
        db.client.clientaddress.upsert(
            where={"id": address.id},
            data={
                "create": {
                    "id": address.id,
                    "clientId": address.client_id,
                    "street": address.street,
                    "streetNumber": address.street_number,
                    "city": address.city,
                    "province": address.province,
                    "latitude": address.latitude,
                    "longitude": address.longitude,
                    "floor": address.floor,
                    "apartment": address.apartment,
                    "postalCode": address.postal_code,
                    "deliveryInstructions": address.delivery_instructions,
                    "label": address.label,
                    "isDefault": address.is_default,
                },
                "update": {
                    "clientId": address.client_id,
                    "street": address.street,
                    "streetNumber": address.street_number,
                    "city": address.city,
                    "province": address.province,
                    "latitude": address.latitude,
                    "longitude": address.longitude,
                    "floor": address.floor,
                    "apartment": address.apartment,
                    "postalCode": address.postal_code,
                    "deliveryInstructions": address.delivery_instructions,
                    "label": address.label,
                    "isDefault": address.is_default,
                },
            },
        )

    def find_by_id(self, address_id: str) -> Address | None:
        record = db.client.clientaddress.find_unique(where={"id": address_id})
        return self._to_domain(record) if record is not None else None

    def find_by_client_id(self, client_id: str) -> list[Address]:
        records = db.client.clientaddress.find_many(where={"clientId": client_id})
        return [self._to_domain(record) for record in records]

    def update(self, address: Address) -> None:
        db.client.clientaddress.update(
            where={"id": address.id},
            data={
                "clientId": address.client_id,
                "street": address.street,
                "streetNumber": address.street_number,
                "city": address.city,
                "province": address.province,
                "latitude": address.latitude,
                "longitude": address.longitude,
                "floor": address.floor,
                "apartment": address.apartment,
                "postalCode": address.postal_code,
                "deliveryInstructions": address.delivery_instructions,
                "label": address.label,
                "isDefault": address.is_default,
            },
        )

    def delete(self, address_id: str) -> None:
        db.client.clientaddress.delete(where={"id": address_id})

    def unset_default_for_client(self, client_id: str) -> None:
        db.client.clientaddress.update_many(
            where={"clientId": client_id, "isDefault": True},
            data={"isDefault": False},
        )

    @staticmethod
    def _to_domain(record) -> Address:
        return Address(
            id=record.id,
            client_id=record.clientId,
            street=record.street,
            street_number=record.streetNumber,
            city=record.city,
            province=record.province,
            latitude=record.latitude,
            longitude=record.longitude,
            floor=record.floor,
            apartment=record.apartment,
            postal_code=record.postalCode,
            delivery_instructions=record.deliveryInstructions,
            label=record.label,
            is_default=record.isDefault,
        )
