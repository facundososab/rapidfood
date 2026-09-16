"""BusinessAddressQueryPort — driven port.

Allows the configure-delivery use case to verify that a chosen origin
address actually belongs to the restaurant being configured.
"""

from __future__ import annotations

from dataclasses import dataclass
from typing import Optional, Protocol


@dataclass(frozen=True)
class AddressSnapshot:
    """Minimal address data needed for ownership verification."""

    address_id: str
    business_config_id: str


class BusinessAddressQueryPort(Protocol):
    """Driven port for querying address ownership."""

    def get_by_id(self, address_id: str) -> Optional[AddressSnapshot]:
        """Return the address snapshot, or None if the address does not exist."""
        ...
