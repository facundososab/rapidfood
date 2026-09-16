"""DemandClassifier — pure domain service.

Classifies the current order count into a DemandLevel and returns
the corresponding multiplier from the pricing configuration.

Rules:
    count < high_demand_threshold          -> NORMAL  (multiplier = 1.00)
    count >= high_demand_threshold
        AND count < very_high_demand_threshold -> HIGH
    count >= very_high_demand_threshold    -> VERY_HIGH
"""

from __future__ import annotations

from decimal import Decimal

from modules.delivery.domain.models.demand_level import DemandLevel
from modules.delivery.domain.models.delivery_pricing_config import DeliveryPricingConfig

_NORMAL_MULTIPLIER = Decimal("1.00")


def classify_demand(
    active_order_count: int,
    pricing_config: DeliveryPricingConfig,
) -> tuple[DemandLevel, Decimal]:
    """Classify demand and return (DemandLevel, multiplier).

    Args:
        active_order_count: Number of recent active delivery orders.
        pricing_config: Per-restaurant pricing configuration.

    Returns:
        Tuple of (DemandLevel, Decimal multiplier to apply to shipping cost).
    """
    if active_order_count >= pricing_config.very_high_demand_threshold:
        return DemandLevel.VERY_HIGH, pricing_config.very_high_demand_multiplier

    if active_order_count >= pricing_config.high_demand_threshold:
        return DemandLevel.HIGH, pricing_config.high_demand_multiplier

    return DemandLevel.NORMAL, _NORMAL_MULTIPLIER
