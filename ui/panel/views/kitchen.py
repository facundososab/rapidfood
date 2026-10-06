"""Vista de cocina: pedidos nuevos y en preparacion"""
from __future__ import annotations

from .common import page
from ..services.factory import get_client
from ..domain import orders as orders_domain


def index(request):
    client = get_client()
    rows = [o for o in client.list_orders(page=1, page_size=100).items if o is not None]

    new_orders = sorted(
        (o for o in rows if o.status == "CONFIRMED"),
        key=lambda o: o.createdAt,
    )
    in_progress_orders = sorted(
        (o for o in rows if o.status == "IN_PREPARATION"),
        key=lambda o: o.createdAt,
    )

    context = {
        "active_section": "kitchen",
        "new_orders": [(o, orders_domain.valid_transitions(o)) for o in new_orders],
        "in_progress_orders": [(o, orders_domain.valid_transitions(o)) for o in in_progress_orders]
    }
    return page(request, "kitchen/index.html", context)

