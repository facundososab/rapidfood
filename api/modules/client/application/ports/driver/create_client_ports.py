from dataclasses import dataclass
from typing import Protocol


@dataclass(frozen=True)
class CreateClientCommand:
    name: str
    last_name: str
    phone_number: str


@dataclass(frozen=True)
class ClientResponse:
    id: str
    name: str
    last_name: str
    phone_number: str


class CreateClientPort(Protocol):
    def execute(self, command: CreateClientCommand) -> ClientResponse: ...
