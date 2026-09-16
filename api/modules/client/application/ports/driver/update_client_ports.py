from dataclasses import dataclass
from typing import Protocol

from .create_client_ports import ClientResponse


@dataclass(frozen=True)
class UpdateClientCommand:
    client_id: str
    name: str
    last_name: str
    phone_number: str


class UpdateClientPort(Protocol):
    def execute(self, command: UpdateClientCommand) -> ClientResponse: ...
