"""Driven port: estimate the preparation time (minutes) for a restaurant.

Implemented by an adapter that reads the restaurant's configuration, counts the
current active orders and classifies demand. The order use cases depend only on
this port, so they never touch the classifier or the config storage directly.
"""
from __future__ import annotations

from typing import Protocol, runtime_checkable


@runtime_checkable
class PreparationTimeEstimatorPort(Protocol):
    def estimate_minutes(self, business_config_id: str) -> int: ...
