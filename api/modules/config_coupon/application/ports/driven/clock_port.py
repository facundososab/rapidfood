"""Clock port (driven/outbound).

Abstracts "what time is it" so expiration logic is deterministic in tests.
The real implementation is a thin wrapper over ``datetime.now(UTC)``.
"""

from __future__ import annotations

from datetime import datetime
from typing import Protocol


class ClockPort(Protocol):
    """Provides the current UTC datetime."""

    def utc_now(self) -> datetime:
        """Return the current UTC datetime."""
        ...