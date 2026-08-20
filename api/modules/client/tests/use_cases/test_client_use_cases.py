import pytest

from modules.client.application.ports.driver.delete_client_ports import (
    DeleteClientCommand,
)
from modules.client.application.ports.driver.get_client_ports import GetClientQuery
from modules.client.application.ports.driver.list_clients_ports import ListClientsQuery
from modules.client.application.use_cases.delete_client_use_case import (
    DeleteClientUseCase,
)
from modules.client.application.use_cases.get_client_use_case import GetClientUseCase
from modules.client.application.use_cases.list_clients_use_case import ListClientsUseCase
from modules.client.domain.errors.client_errors import ClientNotFoundError
from modules.client.domain.models.client import Client


def _client(cid, name="Ana", last="Gómez"):
    return Client(id=cid, name=name, lastName=last, phoneNumber="+5491100000000")


class FakeClientRepo:
    def __init__(self, clients=None):
        self._clients = {c.id: c for c in (clients or [])}

    def find_by_id(self, client_id):
        return self._clients.get(client_id)

    def list(self, search=None):
        rows = list(self._clients.values())
        if search:
            needle = search.lower().strip()
            rows = [c for c in rows if needle in c.name.lower()
                    or needle in c.lastName.lower() or needle in c.phoneNumber]
        return rows

    def delete(self, client_id):
        self._clients.pop(client_id, None)

    def client_exists(self, client_id):
        return client_id in self._clients


def test_delete_client_removes_it():
    repo = FakeClientRepo([_client("c-1"), _client("c-2")])
    result = DeleteClientUseCase(clients=repo).execute(DeleteClientCommand(client_id="c-1"))

    assert result.id == "c-1"
    assert "c-1" not in repo._clients


def test_delete_missing_client_raises_not_found():
    with pytest.raises(ClientNotFoundError):
        DeleteClientUseCase(clients=FakeClientRepo()).execute(
            DeleteClientCommand(client_id="c-1")
        )


def test_get_client_returns_client():
    repo = FakeClientRepo([_client("c-1")])
    client = GetClientUseCase(clients=repo).execute(GetClientQuery(client_id="c-1"))

    assert client.id == "c-1"
    assert client.name == "Ana"


def test_get_missing_client_raises_not_found():
    with pytest.raises(ClientNotFoundError):
        GetClientUseCase(clients=FakeClientRepo()).execute(GetClientQuery(client_id="c-9"))


def test_list_clients_filters_by_search():
    repo = FakeClientRepo([_client("c-1", name="Ana"), _client("c-2", name="Bruno")])
    use_case = ListClientsUseCase(clients=repo)

    assert len(use_case.execute(ListClientsQuery())) == 2
    assert len(use_case.execute(ListClientsQuery(search="bru"))) == 1