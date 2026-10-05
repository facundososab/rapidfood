"""Customer service window (WhatsApp 24h rule) as a pure domain policy.

A window opens/resets with every inbound customer message and stays open for 24
hours. Inside it the business may send free-form text; outside it only an
approved template is allowed. This module is framework-free and side-effect-free
so it can be tested in isolation.
"""
from __future__ import annotations

from datetime import datetime, timedelta
from typing import Iterable, Optional

CUSTOMER_SERVICE_WINDOW: timedelta = timedelta(hours=24)


def _is_customer_message(message) -> bool:
    role = getattr(message, "role", None)
    value = getattr(role, "value", role)
    return str(value) == "USER"


def latest_customer_message_at(messages: Iterable) -> Optional[datetime]:
    latest: Optional[datetime] = None
    for message in messages:
        if not _is_customer_message(message):
            continue
        created_at = getattr(message, "created_at", None)
        if created_at is None:
            continue
        if latest is None or created_at > latest:
            latest = created_at
    return latest


def is_customer_service_window_open(
    messages: Iterable,
    now: datetime,
    window: timedelta = CUSTOMER_SERVICE_WINDOW,
) -> bool:
    """True when a free-form (non-template) message may be sent to the customer."""
    last = latest_customer_message_at(messages)
    if last is None:
        return False
    return (now - last) <= window
