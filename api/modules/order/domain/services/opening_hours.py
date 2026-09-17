"""Opening-hours evaluation.

Derives whether the business is open right now from its configured weekly
intervals. Pure domain logic (no frameworks), timezone-aware for Argentina.
"""
from __future__ import annotations

from datetime import datetime, time
from typing import Any, Iterable, Optional
from zoneinfo import ZoneInfo

BUSINESS_TZ = ZoneInfo("America/Argentina/Buenos_Aires")

_WEEKDAYS = [
    "MONDAY",
    "TUESDAY",
    "WEDNESDAY",
    "THURSDAY",
    "FRIDAY",
    "SATURDAY",
    "SUNDAY",
]


def _field(hour: Any, key: str):
    if isinstance(hour, dict):
        return hour.get(key)
    return getattr(hour, key, None)


def _parse_hour(value: Any) -> Optional[time]:
    if not value:
        return None
    try:
        hh, mm = str(value).split(":")[:2]
        return time(int(hh), int(mm))
    except (ValueError, TypeError):
        return None


def is_open_now(hours: Iterable[Any], now: Optional[datetime] = None) -> bool:
    """True when `now` falls inside any configured interval for today's weekday.

    Supports a single interval per weekday and overnight spans (from > to).
    With no hours configured there is no restriction to enforce, so the business
    is considered open (avoids blocking orders on an unconfigured environment).
    """
    hours = list(hours or [])
    if not hours:
        return True

    now = now or datetime.now(BUSINESS_TZ)
    if now.tzinfo is None:
        now = now.replace(tzinfo=BUSINESS_TZ)
    local = now.astimezone(BUSINESS_TZ)

    today = _WEEKDAYS[local.weekday()]
    current = local.time()

    for hour in hours:
        if _field(hour, "openWeekDay") != today:
            continue
        start = _parse_hour(_field(hour, "openFromHour"))
        end = _parse_hour(_field(hour, "openToHour"))
        if start is None or end is None:
            continue
        if start <= end:
            if start <= current <= end:
                return True
        else:  # overnight span, e.g. 22:00 -> 02:00
            if current >= start or current <= end:
                return True
    return False
