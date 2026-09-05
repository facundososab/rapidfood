from dataclasses import dataclass
from typing import Protocol

from .add_address_ports import AddressResponse


@dataclass(frozen=True)
class SetDefaultAddressCommand:
    address_id: str
    client_id: str


class SetDefaultAddressPort(Protocol):
    def execute(self, command: SetDefaultAddressCommand) -> AddressResponse: ...
