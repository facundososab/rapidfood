import pytest
from unittest.mock import Mock

from modules.client.application.ports.driver.delete_client_ports import (
    DeleteClientCommand,
)
from modules.client.application.use_cases.delete_client_use_case import (
    DeleteClientUseCase,
)
from modules.client.domain.errors.client_errors import ClientNotFoundError
from modules.client.domain.models.client import Client


def _client(cid, name="Ana", last="Gómez"):
    return Client(id=cid, name=name, last_name=last, phone_number="+5491100000000")


def test_delete_client_removes_it():
    mock_repo = Mock()
    mock_repo.client_exists.return_value = True

    use_case = DeleteClientUseCase(clients=mock_repo)
    result = use_case.execute(DeleteClientCommand(client_id="c-1"))

    assert result.id == "c-1"
    mock_repo.delete.assert_called_once_with("c-1")


def test_delete_missing_client_raises_not_found():
    mock_repo = Mock()
    mock_repo.client_exists.return_value = False

    use_case = DeleteClientUseCase(clients=mock_repo)
    
    with pytest.raises(ClientNotFoundError):
        use_case.execute(DeleteClientCommand(client_id="c-1"))
