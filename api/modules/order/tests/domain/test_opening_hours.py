"""Tests for the opening-hours domain service."""

from __future__ import annotations

from datetime import datetime

from modules.order.domain.services.opening_hours import BUSINESS_TZ, is_open_now


def _hours(day: str, start: str, end: str) -> dict:
    return {"openWeekDay": day, "openFromHour": start, "openToHour": end}


# 2026-09-16 is a Wednesday.
def _wednesday(hour: int, minute: int = 0) -> datetime:
    return datetime(2026, 9, 16, hour, minute, tzinfo=BUSINESS_TZ)


def test_no_hours_configured_is_open():
    assert is_open_now([]) is True


def test_inside_interval_is_open():
    assert is_open_now([_hours("WEDNESDAY", "09:00", "18:00")], _wednesday(12)) is True


def test_outside_interval_is_closed():
    assert is_open_now([_hours("WEDNESDAY", "09:00", "18:00")], _wednesday(20)) is False


def test_other_weekday_is_closed():
    assert is_open_now([_hours("THURSDAY", "09:00", "18:00")], _wednesday(12)) is False


def test_overnight_span_covers_next_early_hours():
    assert is_open_now([_hours("WEDNESDAY", "22:00", "02:00")], _wednesday(1)) is True


def test_accepts_objects_with_attributes():
    class Hour:
        openWeekDay = "WEDNESDAY"
        openFromHour = "09:00"
        openToHour = "18:00"

    assert is_open_now([Hour()], _wednesday(12)) is True


def test_naive_datetime_is_assumed_business_timezone():
    assert is_open_now([_hours("WEDNESDAY", "09:00", "18:00")], datetime(2026, 9, 16, 12)) is True
