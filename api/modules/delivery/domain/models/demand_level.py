"""DemandLevel domain enum.

Represents the current demand classification for a restaurant.
This is a derived, ephemeral value — it is never persisted.
"""

from __future__ import annotations

from enum import Enum


class DemandLevel(Enum):
    NORMAL = "NORMAL"
    HIGH = "HIGH"
    VERY_HIGH = "VERY_HIGH"
