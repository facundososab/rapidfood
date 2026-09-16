import pytest
from unittest.mock import Mock

from modules.client.application.ports.driver.list_clients_ports import ListClientsQuery
from modules.client.application.use_cases.list_clients_use_case import ListClientsUseCase
from modules.client.domain.models.client import Client


def _client(cid, name="Ana", last="Gómez"):
    return Client(id=cid, name=name, last_name=last, phone_number="+5491100000000")


def test_list_clients_filters_by_search():
    mock_repo = Mock()
    c1 = _client("c-1", name="Ana")
    c2 = _client("c-2", name="Bruno")
    
    # We simulate what the FakeClientRepo did: return only the matching clients
    # when search="bru", we return c2. when no search, return both.
    def mock_list_side_effect(search=None):
        rows = [c1, c2]
        if search:
            needle = search.lower().strip()
            rows = [c for c in rows if needle in c.name.lower()
                    or needle in c.last_name.lower() or needle in c.phone_number]
        return rows
        
    mock_repo.list.side_effect = mock_list_side_effect

    use_case = ListClientsUseCase(clients=mock_repo)

    assert len(use_case.execute(ListClientsQuery())) == 2
    assert len(use_case.execute(ListClientsQuery(search="bru"))) == 1
