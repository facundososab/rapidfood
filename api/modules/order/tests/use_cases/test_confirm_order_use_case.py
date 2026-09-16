import pytest
from decimal import Decimal
from datetime import date
from unittest.mock import Mock
from modules.order.application.use_cases.confirm_order_use_case import ConfirmOrderUseCase
from modules.order.application.ports.driver.confirm_order_ports import ConfirmOrderCommand
from modules.order.application.ports.driven.catalog_query import (
    VariantContext, ModifierGroupInfo, ModifierOptionInfo, IngredientInfo,
)
from modules.order.application.ports.driven.business_config_query import BusinessConfigSnapshot
from modules.order.domain.models.order import Order
from modules.order.domain.models.order_line import OrderLine
from modules.order.domain.models.order_line_modifier import OrderLineModifier
from modules.order.domain.models.order_state import OrderState
from modules.order.domain.errors.order_errors import ModifierValidationError


def make_order_with_line(modifier_option_ids=None):
    order = Order(
        id="o-1",
        status=OrderState.DRAFT,
        subtotal=Decimal("0"),
        discount=Decimal("0"),
    )
    modifiers = []
    if modifier_option_ids:
        for opt_id in modifier_option_ids:
            modifiers.append(OrderLineModifier(
                id=f"m-{opt_id}",
                order_line_id="line-1",
                modifier_option_id=opt_id,
                option_name_snapshot="",
            ))
    line = OrderLine(
        id="line-1",
        order_id="o-1",
        product_variant_id="v-doble",
        quantity=2,
        unit_price=Decimal("11000"),
        subtotal=Decimal("22000"),
        modifiers=modifiers,
    )
    order.add_line(line)
    return order


def make_catalog_query(variant_price, modifier_groups=()):
    mock = Mock()
    mock.get_variant_context.return_value = VariantContext(
        product_id="p-1",
        product_name="Stacker",
        product_available=True,
        variant_id="v-doble",
        variant_name="Doble",
        variant_available=True,
        current_price=variant_price,
        ingredients=(),
        modifier_groups=modifier_groups,
    )
    return mock


def make_config_query(is_open=True, min_order=Decimal("0"), shipping=Decimal("0")):
    mock = Mock()
    mock.get_config.return_value = BusinessConfigSnapshot(
        is_open=is_open,
        min_order_amount=min_order,
        shipping_cost=shipping,
    )
    return mock


def test_confirm_freezes_prices():
    """
    Variant price at confirmation time (12500) replaces the draft price (11000).
    2 units: subtotal should be 25000.
    """
    order = make_order_with_line()
    mock_repo = Mock()
    mock_repo.get_by_id.return_value = order

    uc = ConfirmOrderUseCase(
        order_repo=mock_repo,
        config_query=make_config_query(),
        catalog_query=make_catalog_query(variant_price=Decimal("12500")),
    )
    uc.execute(ConfirmOrderCommand(order_id="o-1"))

    frozen_line = order.lines[0]
    assert frozen_line.unit_price == Decimal("12500")
    assert frozen_line.subtotal == Decimal("25000")


def test_confirm_freezes_modifier_snapshot():
    extras_group = ModifierGroupInfo(
        group_id="g-extras",
        name="Extras",
        min_selections=0,
        max_selections=3,
        options=(
            ModifierOptionInfo(
                option_id="opt-bacon",
                name="Bacon",
                price_delta=Decimal("1000"),
                available=True,
            ),
        ),
    )
    order = make_order_with_line(modifier_option_ids=["opt-bacon"])
    mock_repo = Mock()
    mock_repo.get_by_id.return_value = order

    uc = ConfirmOrderUseCase(
        order_repo=mock_repo,
        config_query=make_config_query(),
        catalog_query=make_catalog_query(
            variant_price=Decimal("11500"),
            modifier_groups=(extras_group,),
        ),
    )
    uc.execute(ConfirmOrderCommand(order_id="o-1"))

    modifier = order.lines[0].modifiers[0]
    assert modifier.option_name_snapshot == "Bacon"
    assert modifier.price_delta == Decimal("1000")
    # unit_price = 11500 (variant) + 1000 (bacon) = 12500
    assert order.lines[0].unit_price == Decimal("12500")
    # subtotal = 12500 * 2 = 25000
    assert order.lines[0].subtotal == Decimal("25000")


def test_confirm_sets_confirmed_at():
    order = make_order_with_line()
    mock_repo = Mock()
    mock_repo.get_by_id.return_value = order

    uc = ConfirmOrderUseCase(
        order_repo=mock_repo,
        config_query=make_config_query(),
        catalog_query=make_catalog_query(variant_price=Decimal("10000")),
    )
    uc.execute(ConfirmOrderCommand(order_id="o-1"))

    assert order.confirmed_at is not None
    assert order.status.value == "PENDING"
