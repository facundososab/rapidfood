"""ClockPort — driven port for time abstraction.

Isolates datetime.now() so use cases remain deterministic in tests.
Each module that needs a clock owns its own port definition to avoid
cross-module coupling.
"""

from __future__ import annotations

from datetime import datetime
from typing import Protocol


class ClockPort(Protocol):
    """Provides the current UTC datetime."""

    def utc_now(self) -> datetime:
        """Return the current UTC datetime (timezone-aware)."""
        ...
