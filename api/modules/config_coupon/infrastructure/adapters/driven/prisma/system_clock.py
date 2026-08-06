"""SystemClock — real clock adapter for the ClockPort.

Thin wrapper over ``datetime.now(UTC)``. Located in infrastructure because the
domain/application layers must not depend on the current time directly.
"""

from __future__ import annotations

from datetime import datetime, timezone

from modules.config_coupon.application.ports.driven.clock_port import ClockPort


class SystemClock(ClockPort):
    def utc_now(self) -> datetime:
        return datetime.now(timezone.utc)