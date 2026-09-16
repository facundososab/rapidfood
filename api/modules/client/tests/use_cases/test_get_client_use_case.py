import pytest
from unittest.mock import Mock

from modules.client.application.ports.driver.get_client_ports import GetClientQuery
from modules.client.application.use_cases.get_client_use_case import GetClientUseCase
from modules.client.domain.errors.client_errors import ClientNotFoundError
from modules.client.domain.models.client import Client


def _client(cid, name="Ana", last="Gómez"):
    return Client(id=cid, name=name, last_name=last, phone_number="+5491100000000")


def test_get_client_returns_client():
    mock_repo = Mock()
    client_obj = _client("c-1")
    mock_repo.find_by_id.return_value = client_obj

    use_case = GetClientUseCase(clients=mock_repo)
    client = use_case.execute(GetClientQuery(client_id="c-1"))

    assert client.id == "c-1"
    assert client.name == "Ana"


def test_get_missing_client_raises_not_found():
    mock_repo = Mock()
    mock_repo.find_by_id.return_value = None

    use_case = GetClientUseCase(clients=mock_repo)
    
    with pytest.raises(ClientNotFoundError):
        use_case.execute(GetClientQuery(client_id="c-9"))
