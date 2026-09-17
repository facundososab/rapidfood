"""LangChain tools + agent adapter (no LLM, no DB)."""
from __future__ import annotations

import json
from types import SimpleNamespace

import pytest

from modules.conversation.domain.models.agent_execution_context import (
    AgentExecutionContext,
)
from modules.conversation.domain.errors import AgentBusinessError
from modules.conversation.infrastructure.adapters.driver.langchain.tools import (
    build_tools,
)


class FakeUseCase:
    def __init__(self, result=None, error=None):
        self.result = result
        self.error = error
        self.calls = []

    def execute(self, *args):
        self.calls.append(args)
        if self.error:
            raise self.error
        return self.result


def _context(**overrides):
    values = dict(
        business_configuration_id="biz-1",
        conversation_id="conv-1",
        channel="LANGSMITH",
        client_id="client-1",
        external_message_id="msg-1",
    )
    values.update(overrides)
    return AgentExecutionContext(**values)


def _container(**overrides):
    names = [
        "search_products_use_case",
        "get_product_detail_use_case",
        "get_current_order_use_case",
        "add_item_use_case",
        "update_item_use_case",
        "remove_item_use_case",
        "quote_delivery_use_case",
        "set_delivery_use_case",
        "set_pickup_use_case",
        "set_client_use_case",
        "set_payment_type_use_case",
        "apply_coupon_use_case",
        "get_order_summary_use_case",
        "confirm_order_use_case",
        "cancel_order_use_case",
        "create_checkout_use_case",
        "get_latest_active_order_use_case",
    ]
    values = {name: FakeUseCase(result={"ok": True}) for name in names}
    values.update(overrides)
    return SimpleNamespace(**values)


def _tools(context=None):
    context = context or _context()
    container = _container()
    tools = {t.name: t for t in build_tools(container, context)}
    return container, tools, context


def test_exposes_exactly_the_expected_tool_set():
    _, tools, _ = _tools()

    assert set(tools) == {
        "search_products",
        "get_product_detail",
        "get_current_order",
        "add_item",
        "update_item",
        "remove_item",
        "quote_delivery",
        "set_delivery",
        "set_pickup",
        "set_client",
        "set_payment_type",
        "apply_coupon",
        "get_order_summary",
        "confirm_order",
        "cancel_order",
        "create_payment_checkout",
        "get_latest_active_order",
    }
    # No administrative operations are exposed.
    for forbidden in ("create_product", "advance_order", "set_order_status", "reopen_order"):
        assert forbidden not in tools


def test_tools_cannot_override_identity():
    _, tools, _ = _tools()

    for tool in tools.values():
        field_names = set(tool.args.keys())
        assert "business_configuration_id" not in field_names
        assert "business_config_id" not in field_names
        assert "conversation_id" not in field_names
        assert "client_id" not in field_names


def test_search_products_maps_the_query_and_uses_the_context():
    container, tools, context = _tools()

    raw = tools["search_products"].invoke({"query": "stacker"})

    payload = json.loads(raw)
    assert payload["ok"] is True
    command, passed_context = container.search_products_use_case.calls[0]
    assert command.query == "stacker"
    assert passed_context is context


def test_add_item_maps_arguments_and_never_accepts_prices():
    container, tools, _ = _tools()

    tools["add_item"].invoke(
        {
            "product_variant_id": "v-1",
            "quantity": 2,
            "modifier_option_ids": ["o-1"],
            "removed_ingredient_ids": ["i-1"],
        }
    )

    command, _ = container.add_item_use_case.calls[0]
    assert command.product_variant_id == "v-1"
    assert command.quantity == 2
    assert command.modifier_option_ids == ("o-1",)
    assert command.removed_ingredient_ids == ("i-1",)
    for price_field in ("unit_price", "price", "total", "subtotal"):
        assert price_field not in tools["add_item"].args


def test_update_item_line_identity_and_clearing():
    container, tools, _ = _tools()

    tools["update_item"].invoke({"line_id": "l-1", "modifier_option_ids": []})

    command, _ = container.update_item_use_case.calls[0]
    assert command.line_id == "l-1"
    assert command.modifier_option_ids == ()
    assert command.quantity is None


def test_set_payment_type_only_accepts_the_domain_values():
    _, tools, _ = _tools()

    tools["set_payment_type"].invoke({"payment_type": "CASH"})

    with pytest.raises(Exception):
        tools["set_payment_type"].invoke({"payment_type": "CARD"})


def test_quote_delivery_maps_the_address():
    container, tools, _ = _tools()

    tools["quote_delivery"].invoke(
        {"street": "San Juan", "street_number": "3250", "city": "Rosario", "province": "Santa Fe"}
    )

    command, _ = container.quote_delivery_use_case.calls[0]
    assert command.address.street == "San Juan"
    assert command.address.city == "Rosario"


def test_business_errors_become_structured_results():
    container = _container(
        set_delivery_use_case=FakeUseCase(
            error=AgentBusinessError("Fuera de zona", code="DELIVERY_OUTSIDE_ZONE")
        )
    )
    tools = {t.name: t for t in build_tools(container, _context())}

    payload = json.loads(
        tools["set_delivery"].invoke(
            {"street": "Lejos", "street_number": "1", "city": "X", "province": "Y"}
        )
    )

    assert payload["ok"] is False
    assert payload["error"]["code"] == "DELIVERY_OUTSIDE_ZONE"
    assert "Fuera de zona" in payload["error"]["message"]


def test_technical_errors_do_not_leak_details():
    container = _container(
        add_item_use_case=FakeUseCase(error=RuntimeError("secret connection string"))
    )
    tools = {t.name: t for t in build_tools(container, _context())}

    payload = json.loads(tools["add_item"].invoke({"product_variant_id": "v-1", "quantity": 1}))

    assert payload["ok"] is False
    assert payload["error"]["code"] == "TECHNICAL_ERROR"
    assert "secret" not in json.dumps(payload)


def test_create_payment_checkout_delegates_with_the_context():
    container, tools, context = _tools()

    payload = json.loads(tools["create_payment_checkout"].invoke({}))

    assert payload["ok"] is True
    assert container.create_checkout_use_case.calls[0][0] is context


def test_set_client_maps_name_and_phone():
    container, tools, context = _tools()

    payload = json.loads(
        tools["set_client"].invoke({"name": "Facundo Sosa", "phone_number": "341353106"})
    )

    assert payload["ok"] is True
    command, passed_context = container.set_client_use_case.calls[0]
    assert command.name == "Facundo Sosa"
    assert command.phone_number == "341353106"
    assert passed_context is context


def test_set_client_phone_is_optional():
    container, tools, _ = _tools()
    tools["set_client"].invoke({"name": "Facundo"})
    assert container.set_client_use_case.calls[0][0].phone_number is None
