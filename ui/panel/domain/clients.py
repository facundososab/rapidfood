"""Per-client derived metrics computed from relations (calculated, not persisted).

Valid orders exclude DRAFT and CANCELLED (consistent with the average-ticket rule).
"""
from __future__ import annotations

from dataclasses import dataclass
from decimal import Decimal
from typing import List, Optional

from ..services import dtos

D = Decimal
_EXCLUDED = {"DRAFT", "CANCELLED"}


@dataclass
class ClientMetrics:
    order_count: int
    total_spent: Decimal
    avg_ticket: Optional[Decimal]
    last_order_at: object
    conversation_count: int


def client_metrics(client_id: str, orders: List[dtos.Order],
                   conversations: List[dtos.Conversation]) -> ClientMetrics:
    client_orders = [o for o in orders if o.clientId == client_id]
    valid = [o for o in client_orders if o.status not in _EXCLUDED and o.totalAmount is not None]
    total = sum((o.totalAmount for o in valid), D("0"))
    avg = (total / len(valid)).quantize(D("0.01")) if valid else None
    last = max((o.createdAt for o in client_orders), default=None)
    conv = sum(1 for c in conversations if c.clientId == client_id)
    return ClientMetrics(order_count=len(client_orders), total_spent=total,
                         avg_ticket=avg, last_order_at=last, conversation_count=conv)
