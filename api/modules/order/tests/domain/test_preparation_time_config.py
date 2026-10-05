"""Preparation-time (ETA) configuration and demand classifier."""
from __future__ import annotations

import pytest

from modules.order.domain.errors.order_errors import InvalidPreparationTimeConfigError
from modules.order.domain.models.preparation_time_config import PreparationTimeConfig
from modules.order.domain.services.prep_time_classifier import (
    HIGH,
    NORMAL,
    VERY_HIGH,
    prep_level,
    prep_minutes_for,
)


def _config(**overrides) -> PreparationTimeConfig:
    values = dict(
        high_demand_threshold=8,
        very_high_demand_threshold=15,
        normal_prep_minutes=20,
        high_demand_prep_minutes=35,
        very_high_demand_prep_minutes=50,
        buffer_minutes=5,
    )
    values.update(overrides)
    return PreparationTimeConfig(**values)


def test_classifier_picks_minutes_by_threshold_and_adds_the_buffer():
    config = _config()

    assert prep_minutes_for(0, config) == 25  # 20 + 5
    assert prep_minutes_for(7, config) == 25
    assert prep_minutes_for(8, config) == 40  # 35 + 5
    assert prep_minutes_for(14, config) == 40
    assert prep_minutes_for(15, config) == 55  # 50 + 5


def test_levels_are_classified_with_the_config_own_thresholds():
    config = _config()

    assert prep_level(7, config) is NORMAL
    assert prep_level(8, config) is HIGH
    assert prep_level(15, config) is VERY_HIGH


def test_config_rejects_invalid_values():
    with pytest.raises(InvalidPreparationTimeConfigError):
        _config(very_high_demand_threshold=5)  # not > high
    with pytest.raises(InvalidPreparationTimeConfigError):
        _config(normal_prep_minutes=0)
    with pytest.raises(InvalidPreparationTimeConfigError):
        _config(high_demand_prep_minutes=10)  # < normal
    with pytest.raises(InvalidPreparationTimeConfigError):
        _config(very_high_demand_prep_minutes=10)  # < high
    with pytest.raises(InvalidPreparationTimeConfigError):
        _config(buffer_minutes=-1)


def test_default_config_is_valid():
    default = PreparationTimeConfig.default()
    assert default.normal_prep_minutes > 0
    assert default.very_high_demand_threshold > default.high_demand_threshold
