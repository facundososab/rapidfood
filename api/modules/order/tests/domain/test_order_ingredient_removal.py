import pytest
from decimal import Decimal
from unittest.mock import Mock
from modules.order.application.use_cases.add_line_use_case import AddLineUseCase
from modules.order.application.ports.driver.add_line_port import AddLineCommand
from modules.order.application.ports.driven.catalog_query import (
    VariantContext, IngredientInfo,
)
from modules.order.domain.models.order import Order
from modules.order.domain.models.order_state import OrderState
from modules.order.domain.errors.order_errors import InvalidLineError, IngredientNotRemovableError


def make_use_case_with_ingredients(ingredients):
    mock_repo = Mock()
    order = Order(id="o-1", status=OrderState.DRAFT, subtotal=Decimal("0"), discount=Decimal("0"))
    mock_repo.get_by_id.return_value = order

    ctx = VariantContext(
        product_id="p-1",
        product_name="Burger",
        product_available=True,
        variant_id="v-1",
        variant_name="Default",
        variant_available=True,
        current_price=Decimal("10000"),
        ingredients=tuple(ingredients),
        modifier_groups=(),
    )
    mock_catalog = Mock()
    mock_catalog.get_variant_context.return_value = ctx
    return AddLineUseCase(order_repo=mock_repo, catalog_query=mock_catalog)


def test_remove_removable_ingredient_ok():
    uc = make_use_case_with_ingredients([
        IngredientInfo(ingredient_id="ing-lechuga", name="Lechuga", removable=True)
    ])
    resp = uc.add_line(AddLineCommand(
        order_id="o-1",
        product_variant_id="v-1",
        quantity=1,
        removed_ingredient_ids=["ing-lechuga"],
    ))
    assert resp.line_count == 1


def test_remove_non_removable_ingredient_raises():
    uc = make_use_case_with_ingredients([
        IngredientInfo(ingredient_id="ing-pan", name="Pan", removable=False)
    ])
    with pytest.raises(IngredientNotRemovableError):
        uc.add_line(AddLineCommand(
            order_id="o-1",
            product_variant_id="v-1",
            quantity=1,
            removed_ingredient_ids=["ing-pan"],
        ))


def test_remove_ingredient_not_in_variant_raises():
    uc = make_use_case_with_ingredients([
        IngredientInfo(ingredient_id="ing-lechuga", name="Lechuga", removable=True)
    ])
    with pytest.raises(InvalidLineError):
        uc.add_line(AddLineCommand(
            order_id="o-1",
            product_variant_id="v-1",
            quantity=1,
            removed_ingredient_ids=["ing-does-not-exist"],
        ))


def test_duplicate_removed_ingredient_raises():
    uc = make_use_case_with_ingredients([
        IngredientInfo(ingredient_id="ing-lechuga", name="Lechuga", removable=True)
    ])
    with pytest.raises(InvalidLineError):
        uc.add_line(AddLineCommand(
            order_id="o-1",
            product_variant_id="v-1",
            quantity=1,
            removed_ingredient_ids=["ing-lechuga", "ing-lechuga"],  # duplicate
        ))
