"""Create or update the preparation-time (ETA) configuration for a restaurant.

The domain model validates the invariants, so an invalid configuration is never
persisted.
"""
from __future__ import annotations

from modules.order.application.ports.driven.preparation_time_config_repository import (
    PreparationTimeConfigRepositoryPort,
)
from modules.order.application.ports.driver.preparation_time_ports import (
    ConfigurePreparationTimeCommand,
    ConfigurePreparationTimePort,
    PreparationTimeConfigResponse,
    preparation_time_response,
)
from modules.order.domain.models.preparation_time_config import PreparationTimeConfig


class ConfigurePreparationTimeUseCase(ConfigurePreparationTimePort):
    def __init__(self, config_repo: PreparationTimeConfigRepositoryPort) -> None:
        self._config_repo = config_repo

    def execute(
        self, command: ConfigurePreparationTimeCommand
    ) -> PreparationTimeConfigResponse:
        config = PreparationTimeConfig(
            high_demand_threshold=command.high_demand_threshold,
            very_high_demand_threshold=command.very_high_demand_threshold,
            normal_prep_minutes=command.normal_prep_minutes,
            high_demand_prep_minutes=command.high_demand_prep_minutes,
            very_high_demand_prep_minutes=command.very_high_demand_prep_minutes,
            buffer_minutes=command.buffer_minutes,
        )
        self._config_repo.save(command.business_config_id, config)
        return preparation_time_response(
            command.business_config_id, config, is_configured=True
        )
