"""Business config query port — outbound (owned by ``apps.config_coupon``).

Contract only. Hours use ``open_week_day`` as a ``WeekDay`` enum value and
``"HH:MM"`` strings (Prisma has no TIME type — design decision).
"""

from dataclasses import dataclass
from decimal import Decimal
from typing import Protocol


@dataclass(frozen=True)
class BusinessHoursDTO:
    open_week_day: str  # WeekDay value
    open_from_hour: str  # "HH:MM"
    open_to_hour: str


@dataclass(frozen=True)
class AddressDTO:
    address_id: str
    street: str
    street_number: str
    floor: str | None
    apartment: str | None
    city: str
    province: str
    postal_code: str | None


@dataclass(frozen=True)
class BusinessConfigDTO:
    business_name: str
    min_order: Decimal
    shipping_cost: Decimal
    available_zone: str
    addresses: tuple[AddressDTO, ...]
    business_hours: tuple[BusinessHoursDTO, ...]


class BusinessConfigQueryPort(Protocol):
    def get_config(self) -> BusinessConfigDTO | None: ...
    def is_open_at(self, open_week_day: str, time: str) -> bool: ...
    def is_in_coverage_zone(self, address: AddressDTO) -> bool: ...
