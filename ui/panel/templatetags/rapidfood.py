"""Presentation helpers: money/date formatting, short ids, labels, derived states.

Registered as template builtins (see settings.TEMPLATES), so they are available in
every template without {% load %}.
"""
from __future__ import annotations

import re
from datetime import date, datetime, timedelta
from decimal import Decimal

from django import template
from django.utils.safestring import mark_safe

from ..domain import coupons as coupons_domain
from ..services import dtos

register = template.Library()


@register.filter
def money(value) -> str:
    """Argentine peso formatting: $ 1.234,56 — with a non-breaking thin gap."""
    if value in (None, ""):
        return "—"
    if not isinstance(value, Decimal):
        value = Decimal(str(value))
    q = value.quantize(Decimal("0.01"))
    whole, frac = f"{abs(q):.2f}".split(".")
    grouped = ""
    for i, ch in enumerate(reversed(whole)):
        if i and i % 3 == 0:
            grouped = "." + grouped
        grouped = ch + grouped
    sign = "-" if q < 0 else ""
    return f"{sign}$ {grouped},{frac}"


@register.filter
def money_or_dash(value) -> str:
    return "—" if value is None else money(value)


_MONTHS_ES = (
    "ENERO", "FEBRERO", "MARZO", "ABRIL", "MAYO", "JUNIO",
    "JULIO", "AGOSTO", "SEPTIEMBRE", "OCTUBRE", "NOVIEMBRE", "DICIEMBRE",
)


@register.filter
def day_label(value) -> str:
    """Chat date divider: "HOY, 17 DE SEPTIEMBRE" / "AYER, 16 DE SEPTIEMBRE"."""
    if not value:
        return ""
    moment = value.date() if hasattr(value, "date") else value
    today = date.today()
    prefix = ""
    if moment == today:
        prefix = "HOY, "
    elif moment == today - timedelta(days=1):
        prefix = "AYER, "
    return f"{prefix}{moment.day} DE {_MONTHS_ES[moment.month - 1]}"


@register.filter
def initials(value) -> str:
    """Avatar initials from a name: "Facundo Sosa" -> "FS"."""
    parts = [p for p in re.split(r"\s+", str(value or "").strip()) if p]
    return "".join(part[0] for part in parts[:2]).upper() or "?"


@register.filter
def short_id(value) -> str:
    if not value:
        return "—"
    s = str(value)
    tail = s.split("-")[-1]
    return f"#{tail.upper()}"


@register.filter
def datetime_fmt(value) -> str:
    if value is None:
        return "—"
    if isinstance(value, datetime):
        return value.strftime("%d/%m/%Y %H:%M")
    return str(value)


@register.filter
def date_fmt(value) -> str:
    if value is None:
        return "—"
    if isinstance(value, datetime):
        return value.strftime("%d/%m/%Y")
    return str(value)


@register.filter
def date_short_fmt(value) -> str:
    """Short Spanish date: 19 ago 2026 (locale-independent)."""
    if value is None:
        return "—"
    if isinstance(value, datetime):
        month = ("ene feb mar abr may jun jul ago sep oct nov dic".split())[value.month - 1]
        return f"{value.day} {month} {value.year}"
    return str(value)


@register.filter
def time_fmt(value) -> str:
    if value is None:
        return "—"
    if isinstance(value, datetime):
        return value.strftime("%H:%M")
    return str(value)


@register.filter
def time_ago(value) -> str:
    if not isinstance(value, datetime):
        return "—"
    delta = datetime.now() - value
    mins = int(delta.total_seconds() // 60)
    if mins < 1:
        return "recién"
    if mins < 60:
        return f"hace {mins} min"
    hours = mins // 60
    if hours < 24:
        return f"hace {hours} h"
    return f"hace {hours // 24} d"


@register.filter
def client_name(client) -> str:
    if client is None:
        return "Cliente no identificado"
    return f"{client.name} {client.lastName}"


@register.filter
def order_status_label(value) -> str:
    return dtos.ORDER_STATUS_LABELS.get(value, value)


@register.filter
def order_origin_label(value) -> str:
    return dtos.ORDER_ORIGIN_LABELS.get(value, value)


@register.filter
def payment_status_label(value) -> str:
    return dtos.PAYMENT_STATUS_LABELS.get(value, value)


@register.filter
def delivery_type_label(value) -> str:
    if not value:
        return "—"
    return dtos.DELIVERY_TYPE_LABELS.get(value, value)


@register.filter
def payment_type_label(value) -> str:
    if not value:
        return "—"
    return dtos.PAYMENT_TYPE_LABELS.get(value, value)


@register.filter
def weekday_label(value) -> str:
    return dtos.WEEKDAY_LABELS.get(value, value)


@register.filter
def coupon_state(coupon) -> str:
    return coupons_domain.coupon_state(coupon)


@register.filter
def coupon_state_label(coupon) -> str:
    return coupons_domain.coupon_state_label(coupon)


@register.filter
def total_units(order) -> int:
    return sum(line.quantity for line in order.lines)


@register.simple_tag
def querystring(request, **kwargs):
    """Rebuild the query string preserving existing params, overriding kwargs."""
    params = request.GET.copy()
    for key, value in kwargs.items():
        if value is None or value == "":
            params.pop(key, None)
        else:
            params[key] = value
    encoded = params.urlencode()
    return mark_safe(("?" + encoded) if encoded else "")


@register.inclusion_tag("components/icon.html")
def icon(name, cls=None):
    """Render an inline icon: {% icon 'package' 'w-5 h-5' %}."""
    return {"name": name, "cls": cls}


@register.inclusion_tag("components/order_status_badge.html")
def status_badge(status):
    """Render an order status badge: {% status_badge order.status %}."""
    return {"status": status}


@register.filter
def chat_trim(value) -> str:
    """Trim surrounding whitespace of a chat message.

    Message bodies often end with a trailing newline; rendered inside a
    `white-space: pre-wrap` bubble that would show as a blank line.
    """
    return (value or "").strip()


@register.filter
def sin_label(name) -> str:
    """Turn a group name into its "none" choice: "Elegí tu dip" -> "Sin dip"."""
    n = (name or "").strip()
    for prefix in ("Elegí tu ", "Elegí ", "Elige tu ", "Elige "):
        if n.lower().startswith(prefix.lower()):
            n = n[len(prefix):]
            break
    return "Sin " + n if n else "Sin"
