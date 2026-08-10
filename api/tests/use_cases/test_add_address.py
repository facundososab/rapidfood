import pytest
from decimal import Decimal
from modules.client.application.use_cases.add_address_use_case import AddAddressUseCase
from modules.client.application.ports.driver.address_ports import AddAddressCommand
from modules.client.domain.errors.client_errors import ClientNotFoundError
from modules.client.domain.models.client import Client


class MockClientRepo:
    def __init__(self, exists=True):
        self.exists = exists
        
    def find_by_id(self, client_id):
        if self.exists:
            return Client(client_id, "N", "L", "P")
        return None

class MockAddressRepo:
    def __init__(self):
        self.saved_address = None
        self.unset_default_called = False
        
    def save(self, address):
        self.saved_address = address
        
    def unset_default_for_client(self, client_id):
        self.unset_default_called = True

class MockIdGen:
    def generate(self):
        return "addr-1"


def test_add_address_success():
    client_repo = MockClientRepo()
    addr_repo = MockAddressRepo()
    use_case = AddAddressUseCase(client_repo, addr_repo, MockIdGen())
    
    cmd = AddAddressCommand(
        client_id="c1", street="S", street_number="1", city="C", province="P", 
        latitude=Decimal("0"), longitude=Decimal("0"), is_default=True
    )
    resp = use_case.execute(cmd)
    
    assert resp.id == "addr-1"
    assert addr_repo.saved_address.id == "addr-1"
    assert addr_repo.unset_default_called is True


def test_add_address_client_not_found():
    client_repo = MockClientRepo(exists=False)
    addr_repo = MockAddressRepo()
    use_case = AddAddressUseCase(client_repo, addr_repo, MockIdGen())
    
    cmd = AddAddressCommand(
        client_id="c1", street="S", street_number="1", city="C", province="P", 
        latitude=Decimal("0"), longitude=Decimal("0")
    )
    with pytest.raises(ClientNotFoundError):
        use_case.execute(cmd)
