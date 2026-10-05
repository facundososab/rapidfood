"""Prisma-backed active-order demand counter (kitchen load).

Counts orders in CONFIRMED or IN_PREPARATION for a business, regardless of
delivery/pickup: both consume preparation capacity.
"""
from __future__ import annotations

from prisma import Prisma

from modules.order.application.ports.driven.active_order_demand_query import (
    ActiveOrderDemandQuery,
)

_ACTIVE_STATUSES = ["CONFIRMED", "IN_PREPARATION"]


class PrismaActiveOrderDemandQuery(ActiveOrderDemandQuery):
    def __init__(self, db: Prisma) -> None:
        self._db = db

    def count_active_orders(self, business_config_id: str) -> int:
        return self._db.order.count(
            where={
                "businessConfigId": business_config_id,
                "status": {"in": _ACTIVE_STATUSES},
            }
        )
