"""Client capture, address completion and the related agent use case."""
import pytest

from modules.conversation.application.address_defaults import (
    complete_address,
    require_deliverable_address,
)
from modules.conversation.application.ports.driven.business_service import (
    BusinessAddressDTO,
)
from modules.conversation.application.ports.driven.order_service import (
    CurrentOrderDTO,
)
from modules.conversation.application.ports.driver.agent_commands import (
    AddressCommand,
    SetClientCommand,
)
from modules.conversation.application.use_cases.order_mutations import (
    SetClientForConversationOrderUseCase,
)
from modules.conversation.domain.errors import AgentBusinessError
from modules.conversation.domain.models.agent_execution_context import (
    AgentExecutionContext,
)


# --- address completion ---------------------------------------------------
def test_city_and_province_come_from_the_restaurant():
    address = AddressCommand(street="San Juan", street_number="3250")

    completed = complete_address(
        address,
        BusinessAddressDTO(city="Rosario", province="Santa Fe", postal_code="2000"),
    )

    assert completed.city == "Rosario"
    assert completed.province == "Santa Fe"
    assert completed.postal_code == "2000"


def test_explicit_values_win_over_the_restaurant():
    address = AddressCommand(
        street="San Juan", street_number="3250", city="Funes", province="Santa Fe"
    )

    completed = complete_address(
        address, BusinessAddressDTO(city="Rosario", province="Santa Fe")
    )

    assert completed.city == "Funes"


def test_without_restaurant_data_the_address_is_untouched():
    address = AddressCommand(street="San Juan", street_number="3250")
    assert complete_address(address, None) == address


def test_deliverable_address_requires_city_and_province():
    incomplete = AddressCommand(street="San Juan", street_number="3250")
    with pytest.raises(AgentBusinessError) as excinfo:
        require_deliverable_address(incomplete)
    assert excinfo.value.code == "DELIVERY_ADDRESS_REQUIRED"

    complete = complete_address(
        incomplete, BusinessAddressDTO(city="Rosario", province="Santa Fe")
    )
    assert require_deliverable_address(complete) is complete


# --- set_client -----------------------------------------------------------
class FakeOrderService:
    def __init__(self):
        self.calls = []
        self.current = CurrentOrderDTO(
            found=True, order_id="o-1", status="DRAFT", editable=True
        )

    def get_current_order(self, business_config_id, conversation_id):
        return self.current

    def get_or_create_current_draft(self, **kwargs):
        return "o-1"

    def set_client(self, order_id, client_name=None, client_id=None):
        self.calls.append(
            {"order_id": order_id, "client_name": client_name, "client_id": client_id}
        )


class FakeClientService:
    def __init__(self, client_id="client-1"):
        self.client_id = client_id
        self.calls = []

    def resolve_client(self, full_name, phone_number=None):
        self.calls.append((full_name, phone_number))
        return self.client_id


def _context(**overrides):
    values = dict(
        business_configuration_id="biz-1",
        conversation_id="conv-1",
        channel="LANGSMITH",
        external_message_id="msg-1",
    )
    values.update(overrides)
    return AgentExecutionContext(**values)


def test_set_client_links_the_client_when_a_phone_is_given():
    orders = FakeOrderService()
    clients = FakeClientService()
    use_case = SetClientForConversationOrderUseCase(orders, clients)

    result = use_case.execute(
        SetClientCommand(name="Facundo Sosa", phone_number="341353106"), _context()
    )

    assert result["client_linked"] is True
    assert clients.calls == [("Facundo Sosa", "341353106")]
    assert orders.calls[0]["client_name"] == "Facundo Sosa"
    assert orders.calls[0]["client_id"] == "client-1"


def test_set_client_without_a_phone_keeps_only_the_name():
    orders = FakeOrderService()
    clients = FakeClientService()
    use_case = SetClientForConversationOrderUseCase(orders, clients)

    result = use_case.execute(SetClientCommand(name="Facundo"), _context())

    assert result["client_linked"] is False
    assert clients.calls == []
    assert orders.calls[0]["client_id"] is None
    assert orders.calls[0]["client_name"] == "Facundo"


def test_set_client_without_a_client_service_still_saves_the_name():
    orders = FakeOrderService()
    use_case = SetClientForConversationOrderUseCase(orders, None)

    result = use_case.execute(
        SetClientCommand(name="Facundo Sosa", phone_number="341353106"), _context()
    )

    assert result["client_linked"] is False
    assert orders.calls[0]["client_name"] == "Facundo Sosa"
