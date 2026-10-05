"""Preparation-time estimator adapter.

Composes the restaurant's configuration, the current kitchen load and the pure
classifier into the minutes the order use cases need.
"""
from __future__ import annotations

from typing import Any

from modules.order.application.ports.driven.preparation_time_estimator import (
    PreparationTimeEstimatorPort,
)
from modules.order.domain.models.preparation_time_config import PreparationTimeConfig
from modules.order.domain.services.prep_time_classifier import prep_minutes_for


class PreparationTimeEstimator(PreparationTimeEstimatorPort):
    def __init__(self, config_repo: Any, demand_query: Any) -> None:
        self._config_repo = config_repo
        self._demand_query = demand_query

    def estimate_minutes(self, business_config_id: str) -> int:
        config = (
            self._config_repo.get(business_config_id)
            or PreparationTimeConfig.default()
        )
        active_orders = self._demand_query.count_active_orders(business_config_id)
        return prep_minutes_for(active_orders, config)
