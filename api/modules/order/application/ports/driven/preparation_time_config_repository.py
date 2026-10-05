"""Driven port: persistence of a restaurant's preparation-time configuration."""
from __future__ import annotations

from typing import Optional, Protocol, runtime_checkable

from modules.order.domain.models.preparation_time_config import PreparationTimeConfig


@runtime_checkable
class PreparationTimeConfigRepositoryPort(Protocol):
    def get(self, business_config_id: str) -> Optional[PreparationTimeConfig]: ...

    def save(
        self, business_config_id: str, config: PreparationTimeConfig
    ) -> None: ...
