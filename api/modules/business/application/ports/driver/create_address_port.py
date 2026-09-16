from __future__ import annotations

from dataclasses import dataclass
from typing import Optional

@dataclass(frozen=True)
class CreateAddressCommand:
    business_config_id: str
    street: str
    street_number: str
    city: str
    province: str
    floor: Optional[str]
    apartment: Optional[str]
    postal_code: Optional[str]
