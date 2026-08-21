"""OrderDemandAdapter — Prisma-backed driven adapter.

Counts currently active delivery orders for a specific restaurant.
Active = CONFIRMED or IN_PREPARATION (the states that actually load the kitchen).
"""

from __future__ import annotations

import logging

from prisma import Prisma

from modules.delivery.application.ports.driven.order_demand_provider_port import (
    OrderDemandProviderPort,
)

logger = logging.getLogger(__name__)

# Statuses that represent real in-flight kitchen demand.
_ACTIVE_STATUSES = ["CONFIRMED", "IN_PREPARATION"]


class OrderDemandAdapter(OrderDemandProviderPort):
    """Counts active delivery orders using Prisma."""

    def __init__(self, db: Prisma) -> None:
        self._db = db

    def count_active_delivery_orders(
        self,
        business_config_id: str,
    ) -> int:
        """Return count of orders currently in CONFIRMED or IN_PREPARATION."""
        count = self._db.order.count(
            where={
                "businessConfigId": business_config_id,
                "deliveryType": "DELIVERY",
                "status": {"in": _ACTIVE_STATUSES},
            }
        )
        logger.debug(
            "Active demand count for business=%s: %d",
            business_config_id,
            count,
        )
        return count
