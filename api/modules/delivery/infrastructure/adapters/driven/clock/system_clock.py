"""SystemClock — real clock adapter for ClockPort."""

from __future__ import annotations

from datetime import datetime, timezone

from modules.delivery.application.ports.driven.clock_port import ClockPort


class SystemClock(ClockPort):
    """Real implementation: returns the current UTC time."""

    def utc_now(self) -> datetime:
        return datetime.now(timezone.utc)
