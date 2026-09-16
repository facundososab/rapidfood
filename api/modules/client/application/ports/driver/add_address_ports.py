from dataclasses import dataclass
from decimal import Decimal
from typing import Protocol


@dataclass(frozen=True)
class AddAddressCommand:
    client_id: str
    street: str
    street_number: str
    city: str
    province: str
    latitude: Decimal
    longitude: Decimal
    floor: str | None = None
    apartment: str | None = None
    postal_code: str | None = None
    delivery_instructions: str | None = None
    label: str | None = None
    is_default: bool = False


@dataclass(frozen=True)
class AddressResponse:
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


class AddAddressPort(Protocol):
    def execute(self, command: AddAddressCommand) -> AddressResponse: ...
