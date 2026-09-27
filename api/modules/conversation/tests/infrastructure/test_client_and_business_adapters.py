"""Client resolution and business-address adapters (duck-typed stubs)."""
from types import SimpleNamespace

from modules.conversation.infrastructure.adapters.driven.business_service_adapter import (
    BusinessServiceAdapter,
)
from modules.conversation.infrastructure.adapters.driven.client_service_adapter import (
    ClientServiceAdapter,
)


class Stub:
    def __init__(self, result=None, error=None):
        self.result = result
        self.error = error
        self.calls = []

    def execute(self, command):
        self.calls.append(command)
        if self.error:
            raise self.error
        return self.result


# --- client resolution ----------------------------------------------------
def test_existing_client_by_phone_is_reused():
    find = lambda phone: SimpleNamespace(id="client-1")  # noqa: E731
    create = Stub()
    adapter = ClientServiceAdapter(find, create)

    assert adapter.resolve_client("Facundo Sosa", "341353106") == "client-1"
    assert create.calls == []


def test_new_client_with_a_full_name_is_created():
    create = Stub(result=SimpleNamespace(id="client-9"))
    adapter = ClientServiceAdapter(lambda phone: None, create)

    assert adapter.resolve_client("Facundo Sosa", "341353106") == "client-9"
    command = create.calls[0]
    assert command.name == "Facundo"
    assert command.last_name == "Sosa"
    assert command.phone_number == "341353106"


def test_single_word_name_does_not_create_a_client():
    create = Stub(result=SimpleNamespace(id="client-9"))
    adapter = ClientServiceAdapter(lambda phone: None, create)

    assert adapter.resolve_client("Facundo", "341353106") is None
    assert create.calls == []


def test_no_phone_means_no_client():
    adapter = ClientServiceAdapter(lambda phone: None, Stub())
    assert adapter.resolve_client("Facundo Sosa", None) is None
    assert adapter.resolve_client("Facundo Sosa", "  ") is None


def test_creation_race_reuses_the_client_created_meanwhile():
    state = {"first": True}

    def find(phone):
        if state["first"]:
            state["first"] = False
            return None
        return SimpleNamespace(id="client-raced")

    adapter = ClientServiceAdapter(find, Stub(error=RuntimeError("already exists")))

    assert adapter.resolve_client("Facundo Sosa", "341353106") == "client-raced"


# --- business address -----------------------------------------------------
def test_business_address_comes_from_the_first_configured_address():
    get_configuration = Stub(
        result={
            "addresses": [
                {
                    "city": "Rosario",
                    "province": "Santa Fe",
                    "postalCode": "2000",
                    "street": "Córdoba",
                }
            ]
        }
    )
    adapter = BusinessServiceAdapter(get_configuration)

    address = adapter.get_address("biz-1")

    assert address.city == "Rosario"
    assert address.province == "Santa Fe"
    assert address.postal_code == "2000"
    assert get_configuration.calls[0].business_config_id == "biz-1"


def test_business_address_is_none_without_configuration_or_addresses():
    assert BusinessServiceAdapter(Stub(result={"addresses": []})).get_address("b") is None
    assert (
        BusinessServiceAdapter(Stub(error=RuntimeError("not found"))).get_address("b")
        is None
    )
