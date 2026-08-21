from __future__ import annotations

from modules.business.application.ports.driven.business_repository_port import (
    BusinessConfigurationRepositoryPort,
)
from modules.business.application.ports.driver.save_business_configuration_port import (
    SaveBusinessConfigurationCommand,
)
from ._shared import _serialize_config


class SaveBusinessConfigurationUseCase:
    def __init__(self, repo: BusinessConfigurationRepositoryPort) -> None:
        self._repo = repo

    def execute(self, command: SaveBusinessConfigurationCommand) -> dict:
        config = self._repo.save_general(
            command.business_config_id,
            business_name=command.business_name,
            min_order=command.min_order,
            shipping_cost=command.shipping_cost,
        )
        return _serialize_config(config)
