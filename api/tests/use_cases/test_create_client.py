import pytest
from modules.client.application.use_cases.create_client_use_case import CreateClientUseCase
from modules.client.application.ports.driver.client_ports import CreateClientCommand
from modules.client.domain.errors.client_errors import ClientAlreadyExistsError
from modules.client.domain.models.client import Client


class MockClientRepository:
    def __init__(self):
        self.saved_client = None
        self.existing_client = None

    def find_by_phone(self, phone):
        return self.existing_client

    def save(self, client):
        self.saved_client = client


class MockIdGenerator:
    def generate(self):
        return "mock-id"


def test_create_client_success():
    repo = MockClientRepository()
    use_case = CreateClientUseCase(repo, MockIdGenerator())
    
    cmd = CreateClientCommand(name="John", last_name="Doe", phone_number="+123")
    response = use_case.execute(cmd)
    
    assert response.id == "mock-id"
    assert response.name == "John"
    assert repo.saved_client is not None
    assert repo.saved_client.id == "mock-id"


def test_create_client_already_exists():
    repo = MockClientRepository()
    repo.existing_client = Client("existing-id", "Jane", "Doe", "+123")
    use_case = CreateClientUseCase(repo, MockIdGenerator())
    
    cmd = CreateClientCommand(name="John", last_name="Doe", phone_number="+123")
    with pytest.raises(ClientAlreadyExistsError):
        use_case.execute(cmd)
