from dataclasses import dataclass
from decimal import Decimal
from typing import Protocol


@dataclass(frozen=True)
class ClientDTO:
    id: str
    name: str
    last_name: str
    phone_number: str


@dataclass(frozen=True)
class AddressDTO:
    id: str
    client_id: str
    street: str
    street_number: str
    city: str
    province: str
    latitude: Decimal
    longitude: Decimal
    floor: str | None
    apartment: str | None
    postal_code: str | None
    delivery_instructions: str | None
    label: str | None
    is_default: bool


class ClientQueryPort(Protocol):
    def find_by_id(self, client_id: str) -> ClientDTO | None: ...
    
    def find_by_phone_number(self, phone: str) -> ClientDTO | None: ...
    
    def get_address(self, address_id: str) -> AddressDTO | None: ...
