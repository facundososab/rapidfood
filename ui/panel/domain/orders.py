"""Order-related derived values (calculated, not persisted)."""
from __future__ import annotations

from typing import List

from ..services import dtos

ACTIVE_STATUSES = ["PENDING", "PAID", "CONFIRMED", "IN_PREPARATION", "READY"]
COMPLETED_STATUSES = ["DELIVERED", "PICKED_UP"]
# Linear happy-path flow; CANCELLED is shown apart. Orders do not necessarily
# traverse every state.
FLOW_STATUSES = ["DRAFT", "PENDING", "PAID", "CONFIRMED", "IN_PREPARATION", "READY"]
FLOW_TERMINAL = ["DELIVERED", "PICKED_UP"]


def total_units(order: dtos.Order) -> int:
    return sum(line.quantity for line in order.lines)


def is_active(order: dtos.Order) -> bool:
    return order.status in ACTIVE_STATUSES


def is_completed(order: dtos.Order) -> bool:
    return order.status in COMPLETED_STATUSES


def count_by_status(orders: List[dtos.Order]) -> dict:
    counts = {}
    for o in orders:
        counts[o.status] = counts.get(o.status, 0) + 1
    return counts
