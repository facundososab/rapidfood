"""Read the preparation-time (ETA) configuration, falling back to defaults."""
from __future__ import annotations

from modules.order.application.ports.driven.preparation_time_config_repository import (
    PreparationTimeConfigRepositoryPort,
)
from modules.order.application.ports.driver.preparation_time_ports import (
    GetPreparationTimeConfigurationPort,
    PreparationTimeConfigResponse,
    preparation_time_response,
)
from modules.order.domain.models.preparation_time_config import PreparationTimeConfig


class GetPreparationTimeConfigurationUseCase(GetPreparationTimeConfigurationPort):
    def __init__(self, config_repo: PreparationTimeConfigRepositoryPort) -> None:
        self._config_repo = config_repo

    def execute(self, business_config_id: str) -> PreparationTimeConfigResponse:
        stored = self._config_repo.get(business_config_id)
        config = stored or PreparationTimeConfig.default()
        return preparation_time_response(
            business_config_id, config, is_configured=stored is not None
        )
