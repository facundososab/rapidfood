"""Business domain models."""

from __future__ import annotations

from dataclasses import dataclass, field
from typing import Optional


@dataclass(frozen=True)
class Address:
    id: str
    street: str
    streetNumber: str
    city: str
    province: str
    businessConfigId: str
    floor: Optional[str] = None
    apartment: Optional[str] = None
    postalCode: Optional[str] = None

    def full_label(self) -> str:
        parts = [f"{self.street} {self.streetNumber}"]
        if self.floor:
            parts.append(f"Piso {self.floor}")
        if self.apartment:
            parts.append(f"Dpto {self.apartment}")
        parts.append(self.city)
        parts.append(self.province)
        return ", ".join(parts)


@dataclass(frozen=True)
class BusinessHours:
    id: str
    openWeekDay: str   # WeekDay enum value as string
    openFromHour: str  # "HH:MM"
    openToHour: str    # "HH:MM"
    businessConfigId: str


@dataclass
class BusinessConfiguration:
    id: str
    businessName: str
    minOrder: object  # Decimal
    shippingCost: object  # Decimal
    businessHours: list[BusinessHours] = field(default_factory=list)
    addresses: list[Address] = field(default_factory=list)
