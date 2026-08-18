"""Dashboard metrics — all derived (calculated) values.

Key conceptual distinctions required by the brief:
  * Facturación de pedidos  -> based on Order.totalAmount
  * Cobrado online          -> based on Payment.amount where status == APPROVED
These are never conflated.

Average ticket excludes DRAFT and CANCELLED and null totalAmount.
"""
from __future__ import annotations

from dataclasses import dataclass, field
from datetime import datetime, timedelta
from decimal import Decimal
from typing import List, Optional

from ..services import dtos
from . import orders as orders_domain

D = Decimal
_EXCLUDED = {"DRAFT", "CANCELLED"}


@dataclass
class Range:
    key: str
    label: str
    start: datetime
    end: datetime
    bucket: str  # "hour" | "day"


def build_range(key: str, start=None, end=None) -> Range:
    now = datetime.now()
    end_of_day = now.replace(hour=23, minute=59, second=59, microsecond=0)
    start_of_day = now.replace(hour=0, minute=0, second=0, microsecond=0)
    if key == "today":
        return Range("today", "Hoy", start_of_day, end_of_day, "hour")
    if key == "7d":
        return Range("7d", "Últimos 7 días", start_of_day - timedelta(days=6), end_of_day, "day")
    if key == "30d":
        return Range("30d", "Últimos 30 días", start_of_day - timedelta(days=29), end_of_day, "day")
    if key == "custom" and start and end:
        span = (end - start).days
        return Range("custom", "Personalizado", start, end, "hour" if span <= 1 else "day")
    return build_range("7d")


def _in_range(dt, rng: Range) -> bool:
    return dt is not None and rng.start <= dt <= rng.end


@dataclass
class DashboardMetrics:
    # sales
    order_revenue: Decimal            # sum Order.totalAmount (valid)
    online_collected: Decimal         # sum Payment.amount APPROVED
    orders_today: int
    avg_ticket: Optional[Decimal]
    active_orders: int
    delivered: int
    picked_up: int
    cancelled: int
    valid_orders: int
    # flow
    flow: List[tuple] = field(default_factory=list)   # (status, label, count)
    cancelled_count: int = 0
    # series
    series: List[dict] = field(default_factory=list)  # {label, amount, count}
    series_max_amount: Decimal = D("0")
    series_max_count: int = 0
    # top products
    top_products: List[dict] = field(default_factory=list)


def _valid_orders_in_range(all_orders, rng: Range):
    return [o for o in all_orders
            if o.status not in _EXCLUDED and o.totalAmount is not None and _in_range(o.createdAt, rng)]


def compute_dashboard(all_orders: List[dtos.Order], all_payments: List[dtos.Payment],
                      rng: Range) -> DashboardMetrics:
    now = datetime.now()
    start_of_day = now.replace(hour=0, minute=0, second=0, microsecond=0)
    end_of_day = now.replace(hour=23, minute=59, second=59, microsecond=0)

    in_range_orders = [o for o in all_orders if _in_range(o.createdAt, rng)]
    valid = _valid_orders_in_range(all_orders, rng)

    order_revenue = sum((o.totalAmount for o in valid), D("0"))
    online = sum((p.amount for p in all_payments
                  if p.status == "APPROVED" and _in_range(p.createdAt, rng)), D("0"))
    orders_today = sum(1 for o in all_orders if start_of_day <= o.createdAt <= end_of_day)
    avg = (order_revenue / len(valid)).quantize(D("0.01")) if valid else None

    active = sum(1 for o in in_range_orders if o.status in orders_domain.ACTIVE_STATUSES)
    delivered = sum(1 for o in in_range_orders if o.status == "DELIVERED")
    picked_up = sum(1 for o in in_range_orders if o.status == "PICKED_UP")
    cancelled = sum(1 for o in in_range_orders if o.status == "CANCELLED")

    counts = orders_domain.count_by_status(in_range_orders)
    flow = [(s, dtos.ORDER_STATUS_LABELS[s], counts.get(s, 0))
            for s in orders_domain.FLOW_STATUSES + orders_domain.FLOW_TERMINAL]

    m = DashboardMetrics(
        order_revenue=order_revenue, online_collected=online, orders_today=orders_today,
        avg_ticket=avg, active_orders=active, delivered=delivered, picked_up=picked_up,
        cancelled=cancelled, valid_orders=len(valid), flow=flow, cancelled_count=cancelled)

    m.series = _series(valid, rng)
    m.series_max_amount = max((s["amount"] for s in m.series), default=D("0"))
    m.series_max_count = max((s["count"] for s in m.series), default=0)
    m.top_products = _top_products(in_range_orders)
    return m


def _series(valid_orders, rng: Range) -> List[dict]:
    buckets = []
    if rng.bucket == "hour":
        for h in range(0, 24):
            buckets.append((h, f"{h:02d}h"))
        data = {h: {"amount": D("0"), "count": 0} for h, _ in buckets}
        for o in valid_orders:
            h = o.createdAt.hour
            data[h]["amount"] += o.totalAmount
            data[h]["count"] += 1
        # trim to business-relevant hours (10..23) for readability
        return [{"label": lbl, "amount": data[h]["amount"], "count": data[h]["count"]}
                for h, lbl in buckets if 10 <= h <= 23]
    days = (rng.end.date() - rng.start.date()).days
    result = []
    from collections import OrderedDict
    data = OrderedDict()
    for i in range(days + 1):
        d = (rng.start + timedelta(days=i)).date()
        data[d] = {"amount": D("0"), "count": 0}
    for o in valid_orders:
        d = o.createdAt.date()
        if d in data:
            data[d]["amount"] += o.totalAmount
            data[d]["count"] += 1
    for d, vals in data.items():
        result.append({"label": d.strftime("%d/%m"), "amount": vals["amount"], "count": vals["count"]})
    return result


def _top_products(orders_in_range: List[dtos.Order], limit: int = 5) -> List[dict]:
    agg = {}
    for o in orders_in_range:
        if o.status in {"DRAFT", "CANCELLED"}:
            continue
        for line in o.lines:
            prod = line.product
            key = line.productId
            if key not in agg:
                agg[key] = {
                    "description": prod.description if prod else key,
                    "category": prod.category.description if prod and prod.category else "—",
                    "units": 0, "revenue": D("0"),
                }
            agg[key]["units"] += line.quantity
            agg[key]["revenue"] += line.subtotal
    rows = sorted(agg.values(), key=lambda r: r["units"], reverse=True)
    return rows[:limit]


@dataclass
class AttentionItems:
    orders: List[dtos.Order]
    payments: List[dtos.Payment]


def needs_attention(all_orders, all_payments) -> AttentionItems:
    order_states = orders_domain.ACTIVE_STATUSES  # PENDING/PAID/CONFIRMED/IN_PREPARATION/READY
    payment_states = {"PENDING", "REJECTED", "FAILED", "EXPIRED"}
    att_orders = sorted([o for o in all_orders if o.status in order_states],
                        key=lambda o: o.createdAt)
    att_payments = sorted([p for p in all_payments if p.status in payment_states],
                          key=lambda p: p.createdAt, reverse=True)
    return AttentionItems(orders=att_orders, payments=att_payments)
