from dataclasses import dataclass
from decimal import Decimal
from typing import Protocol

from .add_address_ports import AddressResponse


@dataclass(frozen=True)
class UpdateAddressCommand:
    address_id: str
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


class UpdateAddressPort(Protocol):
    def execute(self, command: UpdateAddressCommand) -> AddressResponse: ...
