"""Cross-module adapters: delegation + DTO mapping (duck-typed stubs)."""
from types import SimpleNamespace
from typing import Any

import pytest

from modules.conversation.domain.errors import AgentBusinessError
from modules.conversation.infrastructure.adapters.driven.catalog_service_adapter import (
    CatalogServiceAdapter,
)
from modules.conversation.infrastructure.adapters.driven.delivery_service_adapter import (
    DeliveryServiceAdapter,
)
from modules.conversation.infrastructure.adapters.driven.order_service_adapter import (
    OrderServiceAdapter,
)
from modules.order.application.ports.driven.payment_provider import (
    PaymentProviderError,
)
from modules.order.domain.errors.order_errors import (
    OnlinePaymentRequiredError,
    OrderNotConfirmedError,
    PaymentTypeRequiredError,
)


class StubProductQuery:
    def __init__(self, result=None):
        self.result = result
        self.ids = []

    def find_product(self, product_id):
        self.ids.append(product_id)
        return self.result


class StubUseCase:
    def __init__(self, result=None, error=None):
        self.result = result
        self.error = error
        self.commands = []

    def execute(self, command):
        self.commands.append(command)
        if self.error:
            raise self.error
        return self.result


def _order_adapter(**overrides) -> OrderServiceAdapter:
    def stub(name):
        return overrides.get(name, StubUseCase())

    return OrderServiceAdapter(
        get_current_order=stub("get_current_order"),
        get_latest_active_order=stub("get_latest_active_order"),
        get_order_summary=stub("get_order_summary"),
        get_or_create_current_draft=stub("get_or_create_current_draft"),
        add_item=stub("add_item"),
        update_item=stub("update_item"),
        remove_item=stub("remove_item"),
        set_delivery=stub("set_delivery"),
        set_pickup=stub("set_pickup"),
        set_payment_type=stub("set_payment_type"),
        set_client=stub("set_client"),
        apply_coupon=stub("apply_coupon"),
        confirm_order=stub("confirm_order"),
        cancel_order=stub("cancel_order"),
        create_payment_checkout=stub("create_payment_checkout"),
        cancel_superseded_checkout=stub("cancel_superseded_checkout"),
    )


# --- catalog ---------------------------------------------------------------
def test_catalog_search_maps_and_filters_availability():
    list_products = StubUseCase(
        result=[
            SimpleNamespace(id="p-1", name="Stacker", description="d", state="available", category_id="c-1"),
            SimpleNamespace(id="p-2", name="Viejo", description="d", state="unavailable", category_id="c-1"),
        ]
    )
    adapter = CatalogServiceAdapter(
        list_products=list_products, product_query=StubProductQuery(), get_product=StubUseCase()
    )

    result = adapter.search_products("biz-1", query="stacker", only_available=True)

    assert [p.id for p in result] == ["p-1"]
    assert result[0].available is True
    # Matching moved to the conversation boundary (token + variant aware), so the
    # DB is no longer asked to do a naive full-string search.
    command = list_products.commands[0]
    assert command.search is None


class _PerProductQuery:
    """Returns a snapshot per product id (variant-aware search test)."""

    def __init__(self, variants_by_product):
        self._variants = variants_by_product

    def find_product(self, product_id):
        return SimpleNamespace(
            product_id=product_id,
            name=product_id,
            is_available=True,
            variants=self._variants.get(product_id, ()),
        )


def test_catalog_search_matches_variant_names_across_tokens():
    list_products = StubUseCase(
        result=[
            SimpleNamespace(id="p-coke", name="Coca-Cola", description="Gaseosa Coca-Cola.", state="available", category_id="c-1"),
            SimpleNamespace(id="p-classic", name="Classic Burger", description="Smash burger.", state="available", category_id="c-2"),
        ]
    )
    variants = {
        "p-coke": (
            SimpleNamespace(variant_id="v-500", variant_name="500 ml", price=2200, is_available=True),
            SimpleNamespace(variant_id="v-1500", variant_name="1,5 L", price=4200, is_available=True),
        ),
        "p-classic": (
            SimpleNamespace(variant_id="v-doble", variant_name="Doble", price=9500, is_available=True),
        ),
    }
    adapter = CatalogServiceAdapter(
        list_products=list_products,
        product_query=_PerProductQuery(variants),
        get_product=StubUseCase(),
    )

    assert [p.id for p in adapter.search_products("biz", query="Coca-Cola 500")] == ["p-coke"]
    assert [p.id for p in adapter.search_products("biz", query="Classic Burger Doble")] == ["p-classic"]
    # A token that matches nothing must NOT silently return the whole menu.
    assert adapter.search_products("biz", query="Coca-Cola 9999") == []


def test_catalog_detail_maps_variants_ingredients_and_modifiers():
    snapshot = SimpleNamespace(
        product_id="p-1",
        name="Stacker",
        is_available=True,
        variants=(
            SimpleNamespace(
                variant_id="v-1",
                variant_name="Doble",
                price=1200,
                is_available=True,
                ingredients=(SimpleNamespace(ingredient_id="i-1", name="Cebolla", removable=True),),
            ),
        ),
        modifier_groups=(
            SimpleNamespace(
                group_id="g-1",
                name="Extras",
                min_selections=0,
                max_selections=3,
                options=(SimpleNamespace(option_id="o-1", name="Bacon", price_delta=200, available=True),),
            ),
        ),
    )
    adapter = CatalogServiceAdapter(
        list_products=StubUseCase(),
        product_query=StubProductQuery(result=snapshot),
        get_product=StubUseCase(result=SimpleNamespace(description="La mejor")),
    )

    detail = adapter.get_product_detail("biz-1", "p-1")

    assert detail.description == "La mejor"
    assert detail.variants[0].current_price == "1200"
    assert detail.variants[0].ingredients[0].removable is True
    assert detail.modifier_groups[0].options[0].price_delta == "200"


def test_catalog_detail_returns_none_for_an_unknown_product():
    adapter = CatalogServiceAdapter(
        list_products=StubUseCase(),
        product_query=StubProductQuery(result=None),
        get_product=StubUseCase(),
    )
    assert adapter.get_product_detail("biz-1", "missing") is None


# --- order -----------------------------------------------------------------
def test_order_get_current_order_maps_readiness():
    order = SimpleNamespace(id="o-1", status=SimpleNamespace(value="PENDING"), version=5)
    use_case = StubUseCase(
        result=SimpleNamespace(
            found=True,
            order=order,
            editable=True,
            requires_reopen=True,
            requires_new_order=False,
        )
    )
    adapter = _order_adapter(get_current_order=use_case)

    result = adapter.get_current_order("biz-1", "conv-1")

    assert result.found is True
    assert result.order_id == "o-1"
    assert result.status == "PENDING"
    assert result.requires_reopen is True
    assert use_case.commands[0].business_config_id == "biz-1"


def test_order_get_order_summary_maps_lines():
    summary = SimpleNamespace(
        order_id="o-1",
        status="DRAFT",
        version=2,
        lines=[
            SimpleNamespace(
                line_id="l-1",
                product_variant_id="v-1",
                quantity=2,
                unit_price="1000",
                subtotal="2000",
                modifiers=[{"id": "m-1", "name": "Bacon", "price_delta": "200"}],
                removed_ingredients=[{"id": "r-1", "name": "Cebolla"}],
            )
        ],
        subtotal="2000",
        discount="0",
        shipping_cost=None,
        total_amount="2000",
        delivery_type=None,
        address=None,
        payment_type=None,
        estimated_time=None,
        missing_requirements=["delivery_type"],
    )
    adapter = _order_adapter(get_order_summary=StubUseCase(result=summary))

    result = adapter.get_order_summary("o-1")

    assert result.lines[0].line_id == "l-1"
    assert result.lines[0].modifiers[0].name == "Bacon"
    assert result.lines[0].removed_ingredients[0].name == "Cebolla"
    assert result.missing_requirements == ("delivery_type",)


def test_order_mutation_attempts_the_post_commit_cancellation():
    response = SimpleNamespace(
        order_id="o-1",
        version=3,
        replayed=False,
        line_id="l-1",
        line_count=1,
        total_amount="2000",
        superseded_attempt_ids=("att-1", "att-2"),
    )
    canceller = StubUseCase()
    adapter = _order_adapter(add_item=StubUseCase(result=response), cancel_superseded_checkout=canceller)

    result = adapter.add_item(
        business_config_id="biz-1",
        conversation_id="conv-1",
        external_message_id="msg-1",
        order_id="o-1",
        product_variant_id="v-1",
        quantity=1,
        modifier_option_ids=[],
        removed_ingredient_ids=[],
    )

    assert result.line_id == "l-1"
    assert result.version == 3
    cancelled = sorted(c.payment_attempt_id for c in canceller.commands)
    assert cancelled == ["att-1", "att-2"]


def test_order_mutation_survives_a_failing_cancellation():
    response = SimpleNamespace(
        order_id="o-1",
        version=3,
        replayed=False,
        line_id="l-1",
        line_count=1,
        total_amount="2000",
        superseded_attempt_ids=("att-1",),
    )
    adapter = _order_adapter(
        add_item=StubUseCase(result=response),
        cancel_superseded_checkout=StubUseCase(error=RuntimeError("provider down")),
    )

    result = adapter.add_item(
        business_config_id="biz-1",
        conversation_id=None,
        external_message_id="msg-1",
        order_id="o-1",
        product_variant_id="v-1",
        quantity=1,
        modifier_option_ids=[],
        removed_ingredient_ids=[],
    )

    assert result.order_id == "o-1"


def test_order_draft_creation_is_marked_as_agent():
    draft = StubUseCase(result=SimpleNamespace(order_id="new-order"))
    adapter = _order_adapter(get_or_create_current_draft=draft)

    order_id = adapter.get_or_create_current_draft(
        business_config_id="biz-1", conversation_id="conv-1"
    )

    assert order_id == "new-order"
    # Agent drafts MUST be AGENT origin (confirm waits for settlement).
    assert draft.commands[0].origin == "AGENT"


def test_order_confirm_cancel_and_checkout_map():
    confirm = StubUseCase(result=SimpleNamespace(order_id="o-1", status="PENDING"))
    cancel = StubUseCase(result=SimpleNamespace(order_id="o-1", status="CANCELLED"))
    checkout = StubUseCase(
        result=SimpleNamespace(
            order_id="o-1",
            checkout_url="https://mp/1",
            payment_attempt_id="a-1",
            status="PENDING",
            order_version=7,
        )
    )
    adapter = _order_adapter(
        confirm_order=confirm, cancel_order=cancel, create_payment_checkout=checkout
    )

    assert adapter.confirm_order("o-1").status == "PENDING"
    assert adapter.cancel_order("o-1").status == "CANCELLED"
    assert adapter.create_payment_checkout("o-1").order_version == 7


def test_order_adapter_maps_provider_and_precondition_errors_to_stable_codes():
    cases = [
        (PaymentProviderError("provider down"), "PAYMENT_PROVIDER_ERROR"),
        (PaymentTypeRequiredError("no payment type"), "PAYMENT_TYPE_REQUIRED"),
        (OnlinePaymentRequiredError("cash order"), "ONLINE_PAYMENT_REQUIRED"),
        (OrderNotConfirmedError("draft order"), "ORDER_NOT_CONFIRMED"),
    ]
    for error, expected_code in cases:
        adapter = _order_adapter(create_payment_checkout=StubUseCase(error=error))
        with pytest.raises(AgentBusinessError) as excinfo:
            adapter.create_payment_checkout("o-1")
        assert excinfo.value.code == expected_code


# --- delivery --------------------------------------------------------------
def test_delivery_quote_maps_the_result_and_reuses_the_existing_port():
    quote = StubUseCase(
        result=SimpleNamespace(
            available=True,
            shipping_cost=350,
            distance_km=3.2,
            estimated_duration_minutes=12.0,
            demand_level="LOW",
        )
    )
    adapter = DeliveryServiceAdapter(quote)

    result = adapter.quote_delivery(
        "biz-1",
        {"street": "San Juan", "street_number": "3250", "city": "Rosario", "province": "Santa Fe"},
    )

    assert result.available is True
    assert result.shipping_cost == "350"
    command = quote.commands[0]
    assert command.business_config_id == "biz-1"
    assert command.destination_address.street == "San Juan"


def test_delivery_quote_outside_zone_has_no_cost():
    adapter = DeliveryServiceAdapter(
        StubUseCase(
            result=SimpleNamespace(
                available=False,
                shipping_cost=None,
                distance_km=None,
                estimated_duration_minutes=None,
                demand_level=None,
            )
        )
    )

    result = adapter.quote_delivery(
        "biz-1",
        {"street": "Lejos", "street_number": "1", "city": "Otra", "province": "X"},
    )

    assert result.available is False
    assert result.shipping_cost is None
