"""Get/Configure preparation-time (ETA) configuration use cases."""
from __future__ import annotations

import pytest

from modules.order.application.ports.driver.preparation_time_ports import (
    ConfigurePreparationTimeCommand,
)
from modules.order.application.use_cases.configure_preparation_time_use_case import (
    ConfigurePreparationTimeUseCase,
)
from modules.order.application.use_cases.get_preparation_time_configuration_use_case import (
    GetPreparationTimeConfigurationUseCase,
)
from modules.order.domain.errors.order_errors import InvalidPreparationTimeConfigError


class FakeConfigRepo:
    def __init__(self, stored=None):
        self.stored = stored

    def get(self, business_config_id):
        return self.stored

    def save(self, business_config_id, config):
        self.stored = config


def _command(**overrides) -> ConfigurePreparationTimeCommand:
    values = dict(
        business_config_id="b-1",
        high_demand_threshold=10,
        very_high_demand_threshold=20,
        normal_prep_minutes=15,
        high_demand_prep_minutes=30,
        very_high_demand_prep_minutes=45,
        buffer_minutes=5,
    )
    values.update(overrides)
    return ConfigurePreparationTimeCommand(**values)


def test_get_returns_defaults_when_not_configured():
    result = GetPreparationTimeConfigurationUseCase(FakeConfigRepo()).execute("b-1")

    assert result.is_configured is False
    assert result.normal_prep_minutes == 20
    assert result.buffer_minutes == 5


def test_configure_persists_and_get_returns_the_saved_values():
    repo = FakeConfigRepo()

    saved = ConfigurePreparationTimeUseCase(repo).execute(_command())
    assert saved.is_configured is True
    assert saved.high_demand_threshold == 10

    read = GetPreparationTimeConfigurationUseCase(repo).execute("b-1")
    assert read.is_configured is True
    assert read.very_high_demand_threshold == 20
    assert read.normal_prep_minutes == 15


def test_configure_rejects_an_invalid_configuration():
    with pytest.raises(InvalidPreparationTimeConfigError):
        ConfigurePreparationTimeUseCase(FakeConfigRepo()).execute(
            _command(very_high_demand_threshold=5)
        )
