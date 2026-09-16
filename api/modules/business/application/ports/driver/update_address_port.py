"""Update address driver port."""

from __future__ import annotations

from abc import ABC, abstractmethod
from dataclasses import dataclass
from typing import Optional


@dataclass(frozen=True)
class UpdateAddressCommand:
    business_config_id: str
    address_id: str
    street: str
    street_number: str
    city: str
    province: str
    floor: Optional[str]
    apartment: Optional[str]
    postal_code: Optional[str]


class UpdateAddressPort(ABC):
    @abstractmethod
    def execute(self, command: UpdateAddressCommand) -> dict:
        ...
