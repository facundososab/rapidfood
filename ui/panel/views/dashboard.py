from datetime import datetime

from django.shortcuts import render

from ..domain import metrics as metrics_domain
from ..services.factory import get_client


def _parse_date(value):
    if not value:
        return None
    try:
        return datetime.strptime(value, "%Y-%m-%d")
    except ValueError:
        return None


def index(request):
    client = get_client()
    range_key = request.GET.get("range", "7d")
    start = _parse_date(request.GET.get("start"))
    end = _parse_date(request.GET.get("end"))
    if end:
        end = end.replace(hour=23, minute=59, second=59)
    rng = metrics_domain.build_range(range_key, start, end)

    orders = client.all_orders()
    payments = client.all_payments()
    m = metrics_domain.compute_dashboard(orders, payments, rng)
    attention = metrics_domain.needs_attention(orders, payments)

    recent = sorted(orders, key=lambda o: o.createdAt, reverse=True)[:6]

    ctx = {
        "active_section": "dashboard",
        "range": rng,
        "range_key": range_key,
        "m": m,
        "attention": attention,
        "recent": recent,
        "range_options": [("today", "Hoy"), ("7d", "Últimos 7 días"), ("30d", "Últimos 30 días")],
    }
    template = "dashboard/partials/body.html" if request.headers.get("HX-Request") else "dashboard/index.html"
    return render(request, template, ctx)
