from modules.client.application.ports.driver.client_query_port import (
    AddressDTO,
    ClientDTO,
    ClientQueryPort,
)
from shared.infrastructure.prisma.db import db


class PrismaClientQueryAdapter(ClientQueryPort):
    def find_by_id(self, client_id: str) -> ClientDTO | None:
        record = db.client.client.find_unique(where={"id": client_id})
        if record is None:
            return None
        return ClientDTO(
            id=record.id,
            name=record.name,
            last_name=record.lastName,
            phone_number=record.phoneNumber,
        )

    def find_by_phone_number(self, phone: str) -> ClientDTO | None:
        record = db.client.client.find_first(where={"phoneNumber": phone})
        if record is None:
            return None
        return ClientDTO(
            id=record.id,
            name=record.name,
            last_name=record.lastName,
            phone_number=record.phoneNumber,
        )

    def get_address(self, address_id: str) -> AddressDTO | None:
        record = db.client.clientaddress.find_unique(where={"id": address_id})
        if record is None:
            return None
        return AddressDTO(
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
