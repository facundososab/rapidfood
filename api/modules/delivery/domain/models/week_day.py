"""WeekDay domain enum.

Mirrors the Prisma WeekDay enum without importing from prisma.enums.
The adapter layer is responsible for converting between both representations.
"""

from __future__ import annotations

from enum import Enum


class WeekDay(Enum):
    MONDAY = "MONDAY"
    TUESDAY = "TUESDAY"
    WEDNESDAY = "WEDNESDAY"
    THURSDAY = "THURSDAY"
    FRIDAY = "FRIDAY"
    SATURDAY = "SATURDAY"
    SUNDAY = "SUNDAY"
