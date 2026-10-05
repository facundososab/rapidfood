"""Prisma-backed preparation-time configuration repository."""
from __future__ import annotations

from typing import Optional

from prisma import Prisma

from modules.order.application.ports.driven.preparation_time_config_repository import (
    PreparationTimeConfigRepositoryPort,
)
from modules.order.domain.models.preparation_time_config import PreparationTimeConfig


class PrismaPreparationTimeConfigRepository(PreparationTimeConfigRepositoryPort):
    def __init__(self, db: Prisma) -> None:
        self._db = db

    def get(self, business_config_id: str) -> Optional[PreparationTimeConfig]:
        row = self._db.preparationtimeconfiguration.find_unique(
            where={"businessConfigId": business_config_id}
        )
        if row is None:
            return None
        return PreparationTimeConfig(
            high_demand_threshold=row.highDemandThreshold,
            very_high_demand_threshold=row.veryHighDemandThreshold,
            normal_prep_minutes=row.normalPrepMinutes,
            high_demand_prep_minutes=row.highDemandPrepMinutes,
            very_high_demand_prep_minutes=row.veryHighDemandPrepMinutes,
            buffer_minutes=row.bufferMinutes,
        )

    def save(self, business_config_id: str, config: PreparationTimeConfig) -> None:
        data = {
            "highDemandThreshold": config.high_demand_threshold,
            "veryHighDemandThreshold": config.very_high_demand_threshold,
            "normalPrepMinutes": config.normal_prep_minutes,
            "highDemandPrepMinutes": config.high_demand_prep_minutes,
            "veryHighDemandPrepMinutes": config.very_high_demand_prep_minutes,
            "bufferMinutes": config.buffer_minutes,
        }
        self._db.preparationtimeconfiguration.upsert(
            where={"businessConfigId": business_config_id},
            data={
                "create": {"businessConfigId": business_config_id, **data},
                "update": data,
            },
        )
