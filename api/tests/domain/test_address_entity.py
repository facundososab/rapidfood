import pytest
from decimal import Decimal
from modules.client.domain.models.address import Address


def test_create_address_success():
    address = Address.create(
        address_id="1",
        client_id="c1",
        street=" Main St ",
        street_number=" 123 ",
        city=" City ",
        province=" Prov ",
        latitude=Decimal("12.34"),
        longitude=Decimal("56.78"),
    )
    assert address.id == "1"
    assert address.street == "Main St"
    assert address.street_number == "123"

def test_mark_as_default():
    address = Address.create(
        address_id="1", client_id="c1", street="A", street_number="1", 
        city="B", province="C", latitude=Decimal("0"), longitude=Decimal("0")
    )
    assert not address.is_default
    address.mark_as_default()
    assert address.is_default
