from __future__ import annotations

from dataclasses import dataclass

@dataclass(frozen=True)
class DeleteAddressCommand:
    business_config_id: str
    address_id: str
