"""Preparation-time classifier — pure domain service.

Classifies the current active-order count into a preparation time using the
restaurant's OWN thresholds (independent from delivery pricing), then adds the
fixed buffer (waiting / batched deliveries).
"""
from __future__ import annotations

from modules.order.domain.models.preparation_time_config import PreparationTimeConfig

NORMAL = "NORMAL"
HIGH = "HIGH"
VERY_HIGH = "VERY_HIGH"


def prep_level(active_order_count: int, config: PreparationTimeConfig) -> str:
    if active_order_count >= config.very_high_demand_threshold:
        return VERY_HIGH
    if active_order_count >= config.high_demand_threshold:
        return HIGH
    return NORMAL


def prep_minutes_for(
    active_order_count: int, config: PreparationTimeConfig
) -> int:
    """Preparation minutes (level base + buffer) for the current demand."""
    level = prep_level(active_order_count, config)
    if level is VERY_HIGH:
        base = config.very_high_demand_prep_minutes
    elif level is HIGH:
        base = config.high_demand_prep_minutes
    else:
        base = config.normal_prep_minutes
    return base + config.buffer_minutes
