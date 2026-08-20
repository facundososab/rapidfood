from dataclasses import dataclass
from typing import Protocol

from modules.client.domain.models.client import Client


@dataclass(frozen=True)
class ListClientsQuery:
    search: str | None = None


class ListClientsPort(Protocol):
    def execute(self, query: ListClientsQuery) -> list[Client]: ...