import pytest
from modules.client.domain.models.client import Client


def test_create_client_success():
    client = Client.create(
        client_id="123",
        name="  John  ",
        last_name=" Doe ",
        phone_number=" +123456 ",
    )
    assert client.id == "123"
    assert client.name == "John"
    assert client.last_name == "Doe"
    assert client.phone_number == "+123456"

def test_create_client_empty_name():
    with pytest.raises(ValueError):
        Client.create("123", "   ", "Doe", "+123")

def test_update_client_success():
    client = Client(id="123", name="John", last_name="Doe", phone_number="+123")
    client.update(name="Jane", last_name="Smith", phone_number="+987")
    assert client.name == "Jane"
    assert client.last_name == "Smith"
    assert client.phone_number == "+987"
