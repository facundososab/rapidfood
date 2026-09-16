import pytest
from decimal import Decimal
from unittest.mock import Mock
from modules.order.application.use_cases.add_line_use_case import AddLineUseCase
from modules.order.application.ports.driver.add_line_port import AddLineCommand
from modules.order.application.ports.driven.catalog_query import (
    VariantContext, IngredientInfo, ModifierGroupInfo, ModifierOptionInfo,
)
from modules.order.domain.models.order import Order
from modules.order.domain.models.order_state import OrderState
from modules.order.domain.errors.order_errors import InvalidLineError, ModifierValidationError


def make_context(modifier_groups=(), ingredients=()):
    return VariantContext(
        product_id="p-1",
        product_name="Stacker",
        product_available=True,
        variant_id="v-doble",
        variant_name="Doble",
        variant_available=True,
        current_price=Decimal("11000"),
        ingredients=ingredients,
        modifier_groups=modifier_groups,
    )


def make_use_case(context):
    mock_repo = Mock()
    order = Order(id="o-1", status=OrderState.DRAFT, subtotal=Decimal("0"), discount=Decimal("0"))
    mock_repo.get_by_id.return_value = order
    mock_catalog = Mock()
    mock_catalog.get_variant_context.return_value = context
    return AddLineUseCase(order_repo=mock_repo, catalog_query=mock_catalog), mock_repo


def test_add_line_no_modifiers_ok():
    ctx = make_context()
    uc, _ = make_use_case(ctx)
    resp = uc.add_line(AddLineCommand(order_id="o-1", product_variant_id="v-doble", quantity=1))
    assert resp.line_count == 1


def test_modifier_from_correct_product_ok():
    extras_group = ModifierGroupInfo(
        group_id="g-extras",
        name="Extras",
        min_selections=0,
        max_selections=3,
        options=(
            ModifierOptionInfo(option_id="opt-bacon", name="Bacon", price_delta=Decimal("1000"), available=True),
        ),
    )
    ctx = make_context(modifier_groups=(extras_group,))
    uc, _ = make_use_case(ctx)
    resp = uc.add_line(AddLineCommand(
        order_id="o-1",
        product_variant_id="v-doble",
        quantity=1,
        modifier_option_ids=["opt-bacon"],
    ))
    assert resp.line_count == 1


def test_modifier_not_in_product_raises():
    ctx = make_context()  # no modifier groups
    uc, _ = make_use_case(ctx)
    with pytest.raises(ModifierValidationError):
        uc.add_line(AddLineCommand(
            order_id="o-1",
            product_variant_id="v-doble",
            quantity=1,
            modifier_option_ids=["opt-does-not-exist"],
        ))


def test_unavailable_modifier_raises():
    extras_group = ModifierGroupInfo(
        group_id="g-extras",
        name="Extras",
        min_selections=0,
        max_selections=3,
        options=(
            ModifierOptionInfo(option_id="opt-bacon", name="Bacon", price_delta=Decimal("1000"), available=False),
        ),
    )
    ctx = make_context(modifier_groups=(extras_group,))
    uc, _ = make_use_case(ctx)
    with pytest.raises(ModifierValidationError):
        uc.add_line(AddLineCommand(
            order_id="o-1",
            product_variant_id="v-doble",
            quantity=1,
            modifier_option_ids=["opt-bacon"],
        ))


def test_exceeds_max_selections_raises():
    extras_group = ModifierGroupInfo(
        group_id="g-extras",
        name="Extras",
        min_selections=0,
        max_selections=1,  # only 1 allowed
        options=(
            ModifierOptionInfo(option_id="opt-bacon", name="Bacon", price_delta=Decimal("1000"), available=True),
            ModifierOptionInfo(option_id="opt-cheese", name="Cheese", price_delta=Decimal("500"), available=True),
        ),
    )
    ctx = make_context(modifier_groups=(extras_group,))
    uc, _ = make_use_case(ctx)
    with pytest.raises(ModifierValidationError):
        uc.add_line(AddLineCommand(
            order_id="o-1",
            product_variant_id="v-doble",
            quantity=1,
            modifier_option_ids=["opt-bacon", "opt-cheese"],  # 2 but max is 1
        ))


def test_duplicate_modifier_raises():
    extras_group = ModifierGroupInfo(
        group_id="g-extras",
        name="Extras",
        min_selections=0,
        max_selections=3,
        options=(
            ModifierOptionInfo(option_id="opt-bacon", name="Bacon", price_delta=Decimal("1000"), available=True),
        ),
    )
    ctx = make_context(modifier_groups=(extras_group,))
    uc, _ = make_use_case(ctx)
    with pytest.raises(ModifierValidationError):
        uc.add_line(AddLineCommand(
            order_id="o-1",
            product_variant_id="v-doble",
            quantity=1,
            modifier_option_ids=["opt-bacon", "opt-bacon"],  # duplicate
        ))
