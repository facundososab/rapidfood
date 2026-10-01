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

def valid_transitions(order: dtos.Order) -> list[tuple[str, str]]:
    """"Proximos estados validos (status, label) para este pedido, segun  docs/order-state-machine.md.
    CANCELLED queda fuera a proposito, ya que ya existe un boton de cancelar separado con sus reglas"""
    status = order.status
    payment_type = order.paymentType

    if status == "DRAFT":
        return [("PENDING", "Confirmar pedido")]
    if status == "PENDING":
        options = []
        if payment_type in (None, "ONLINE"):
            options.append(("PAID", "Marcar como pagado"))
        if payment_type in (None, "CASH"):
            options.append(("CONFIRMED", "Confirmar (efectivo)"))
        return options
    if status == "PAID":
        return [("CONFIRMED", "Aceptar pedido")]
    if status == "CONFIRMED":
        return [("IN_PREPARATION", "Marcar como en preparación")]
    if status == "IN_PREPARATION":
        return [("READY", "Marcar como listo")]
    if status == "READY":
        if order.deliveryType == "DELIVERY":
            return [("DELIVERED", "Marcar como entregado")]
        return [("PICKED_UP", "Marcar como retirado")]
    return []
