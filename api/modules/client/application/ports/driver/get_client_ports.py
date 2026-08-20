from dataclasses import dataclass
from typing import Protocol

from modules.client.domain.models.client import Client


@dataclass(frozen=True)
class GetClientQuery:
    client_id: str


class GetClientPort(Protocol):
    def execute(self, query: GetClientQuery) -> Client: ...