from __future__ import annotations

from modules.business.application.ports.driven.business_repository_port import (
    BusinessConfigurationRepositoryPort,
)
from modules.business.application.ports.driver.get_business_configuration_port import (
    GetBusinessConfigurationQuery,
)
from modules.business.domain.errors.business_errors import (
    BusinessConfigurationNotFoundError,
)
from ._shared import _serialize_config


class GetBusinessConfigurationUseCase:
    def __init__(self, repo: BusinessConfigurationRepositoryPort) -> None:
        self._repo = repo

    def execute(self, query: GetBusinessConfigurationQuery) -> dict:
        config = self._repo.get_by_id(query.business_config_id)
        if config is None:
            raise BusinessConfigurationNotFoundError(query.business_config_id)
        return _serialize_config(config)
