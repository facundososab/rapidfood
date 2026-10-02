"""Driven port: current kitchen load for a restaurant.

Counts orders that actually load the kitchen (CONFIRMED + IN_PREPARATION),
regardless of delivery/pickup: both consume preparation capacity.
"""
from __future__ import annotations

from typing import Protocol, runtime_checkable


@runtime_checkable
class ActiveOrderDemandQuery(Protocol):
    def count_active_orders(self, business_config_id: str) -> int: ...
