import pytest
from decimal import Decimal
from modules.catalog.domain.models.modifier_group import ModifierGroup
from modules.catalog.domain.models.modifier_option import ModifierOption
from modules.catalog.domain.errors.catalog_errors import InvalidModifierGroupError


def test_valid_modifier_group():
    group = ModifierGroup(
        id="g-1",
        product_id="p-1",
        name="Extras",
        min_selections=0,
        max_selections=3,
    )
    assert group.min_selections == 0
    assert group.max_selections == 3


def test_modifier_group_min_negative_raises():
    with pytest.raises((InvalidModifierGroupError, ValueError)):
        ModifierGroup(id="g-1", product_id="p-1", name="X", min_selections=-1, max_selections=3)


def test_modifier_group_max_zero_raises():
    with pytest.raises((InvalidModifierGroupError, ValueError)):
        ModifierGroup(id="g-1", product_id="p-1", name="X", min_selections=0, max_selections=0)


def test_modifier_group_max_less_than_min_raises():
    with pytest.raises((InvalidModifierGroupError, ValueError)):
        ModifierGroup(id="g-1", product_id="p-1", name="X", min_selections=3, max_selections=2)


def test_modifier_option_negative_price_delta_raises():
    with pytest.raises(ValueError):
        ModifierOption(
            id="o-1",
            modifier_group_id="g-1",
            name="Extra cheese",
            price_delta=Decimal("-1"),
        )


def test_modifier_option_zero_price_delta_ok():
    option = ModifierOption(
        id="o-1",
        modifier_group_id="g-1",
        name="No extras",
        price_delta=Decimal("0"),
    )
    assert option.price_delta == Decimal("0")
