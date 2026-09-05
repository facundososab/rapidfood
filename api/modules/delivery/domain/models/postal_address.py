"""PostalAddress value object.

Built from the Address fields already present in the Prisma schema.
Floor and apartment are NOT used for geocoding — they locate a unit inside
a building, not the building's street position.
"""

from __future__ import annotations

from dataclasses import dataclass
from typing import Optional


@dataclass(frozen=True)
class PostalAddress:
    """Street address used for geocoding. Apartment/floor are excluded."""

    street: str
    street_number: str
    city: str
    province: str
    floor: Optional[str] = None
    apartment: Optional[str] = None
    postal_code: Optional[str] = None

    def geocoding_query(self) -> str:
        """Build a human-readable string for the geocoding provider."""
        parts = [f"{self.street} {self.street_number}", self.city, self.province]
        if self.postal_code:
            parts.append(self.postal_code)
        return ", ".join(parts)
