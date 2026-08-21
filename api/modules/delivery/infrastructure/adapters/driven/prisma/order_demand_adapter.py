"""OrderDemandAdapter — Prisma-backed driven adapter.

Counts recent active delivery orders for a specific restaurant.
Only counts statuses that represent in-flight demand
(PENDING, PAID, CONFIRMED, IN_PREPARATION, READY).
"""

from __future__ import annotations

import logging
from datetime import datetime
from typing import List

from prisma import Prisma

from modules.delivery.application.ports.driven.order_demand_provider_port import (
    OrderDemandProviderPort,
)

logger = logging.getLogger(__name__)

# Order statuses that represent real in-flight demand for a restaurant.
_ACTIVE_STATUSES = ["PENDING", "PAID", "CONFIRMED", "IN_PREPARATION", "READY"]


class OrderDemandAdapter(OrderDemandProviderPort):
    """Counts active delivery orders using Prisma."""

    def __init__(self, db: Prisma) -> None:
        self._db = db

    def count_recent_active_delivery_orders(
        self,
        business_config_id: str,
        since: datetime,
    ) -> int:
        """Return count of active DELIVERY orders created after `since`."""
        count = self._db.order.count(
            where={
                "businessConfigId": business_config_id,
                "deliveryType": "DELIVERY",
                "createdAt": {"gte": since},
                "status": {"in": _ACTIVE_STATUSES},
            }
        )
        logger.debug(
            "Demand count for business=%s since=%s: %d",
            business_config_id,
            since.isoformat(),
            count,
        )
        return count
