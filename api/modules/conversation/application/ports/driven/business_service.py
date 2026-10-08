"""Driven port: business configuration data the agent needs.

Currently only the restaurant's own address, used to complete a delivery address
the customer gave partially (street + number are enough; the city and province
are the restaurant's). The concrete adapter delegates to the business module's
public query port.
"""
from __future__ import annotations

from dataclasses import dataclass
from typing import Optional, Protocol


@dataclass(frozen=True, slots=True)
class BusinessAddressDTO:
    city: Optional[str] = None
    province: Optional[str] = None
    postal_code: Optional[str] = None


class BusinessServicePort(Protocol):
    def get_address(
        self, business_configuration_id: str
    ) -> Optional[BusinessAddressDTO]: ...

    def get_name(self, business_configuration_id: str) -> Optional[str]: ...
