"""Driver ports for reading and configuring the preparation-time (ETA) setup."""
from __future__ import annotations

from abc import ABC, abstractmethod
from dataclasses import dataclass

from modules.order.domain.models.preparation_time_config import PreparationTimeConfig


@dataclass
class ConfigurePreparationTimeCommand:
    business_config_id: str
    high_demand_threshold: int
    very_high_demand_threshold: int
    normal_prep_minutes: int
    high_demand_prep_minutes: int
    very_high_demand_prep_minutes: int
    buffer_minutes: int


@dataclass(frozen=True)
class PreparationTimeConfigResponse:
    business_config_id: str
    high_demand_threshold: int
    very_high_demand_threshold: int
    normal_prep_minutes: int
    high_demand_prep_minutes: int
    very_high_demand_prep_minutes: int
    buffer_minutes: int
    # False when the business has no row yet and defaults are being returned.
    is_configured: bool


class GetPreparationTimeConfigurationPort(ABC):
    @abstractmethod
    def execute(self, business_config_id: str) -> PreparationTimeConfigResponse: ...


class ConfigurePreparationTimePort(ABC):
    @abstractmethod
    def execute(
        self, command: ConfigurePreparationTimeCommand
    ) -> PreparationTimeConfigResponse: ...


def preparation_time_response(
    business_config_id: str,
    config: PreparationTimeConfig,
    *,
    is_configured: bool,
) -> PreparationTimeConfigResponse:
    return PreparationTimeConfigResponse(
        business_config_id=business_config_id,
        high_demand_threshold=config.high_demand_threshold,
        very_high_demand_threshold=config.very_high_demand_threshold,
        normal_prep_minutes=config.normal_prep_minutes,
        high_demand_prep_minutes=config.high_demand_prep_minutes,
        very_high_demand_prep_minutes=config.very_high_demand_prep_minutes,
        buffer_minutes=config.buffer_minutes,
        is_configured=is_configured,
    )
