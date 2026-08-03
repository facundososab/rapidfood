"""Client command port — outbound (owned by ``apps.client``).

Contract only: the agent registers clients through this port. No implementation;
the Prisma repository implements it later.
"""

from typing import Protocol

from apps.client.application.ports.outbound.client_query_port import ClientDTO


class ClientCommandPort(Protocol):
    def create(self, name: str, last_name: str, phone_number: str) -> ClientDTO: ...
