"""Client query port — outbound (owned by ``apps.client``).

Contract only: no implementation. Adapters (``apps.client.adapters.outbound.prisma``)
implement this Protocol and keep all row → DTO mapping inside the adapter.
"""

from dataclasses import dataclass
from typing import Protocol


@dataclass(frozen=True)
class ClientDTO:
    client_id: str
    name: str
    last_name: str
    phone_number: str


class ClientQueryPort(Protocol):
    def find_by_id(self, client_id: str) -> ClientDTO | None: ...
    def find_by_phone_number(self, phone_number: str) -> ClientDTO | None: ...
