"""Adapts the client module's application port to the order module's ClientQuery."""
from __future__ import annotations

from typing import Optional

from modules.client.application.ports.driver.client_query_port import ClientQueryPort
from modules.order.application.ports.driven.client_query import ClientInfo, ClientQuery


class ClientQueryAdapter(ClientQuery):
    def __init__(self, client_query: ClientQueryPort) -> None:
        self._client_query = client_query

    def check_client_exists(self, client_id: str) -> bool:
        return self._client_query.find_by_id(client_id) is not None

    def get_client(self, client_id: str) -> Optional[ClientInfo]:
        dto = self._client_query.find_by_id(client_id)
        if dto is None:
            return None
        return ClientInfo(
            id=dto.id,
            name=dto.name,
            last_name=dto.last_name,
            phone_number=dto.phone_number,
        )
