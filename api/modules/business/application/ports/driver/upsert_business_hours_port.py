from __future__ import annotations

from dataclasses import dataclass

@dataclass(frozen=True)
class BusinessHoursInput:
    open_week_day: str   # e.g. "MONDAY"
    open_from_hour: str  # "HH:MM"
    open_to_hour: str    # "HH:MM"

@dataclass(frozen=True)
class UpsertBusinessHoursCommand:
    business_config_id: str
    hours: list[BusinessHoursInput]
