"""Delivery destination value object.

Captured as a snapshot on the order (not a reference to a mutable address) so the
delivery history stays immutable and anonymous POS deliveries are supported.
"""
from dataclasses import dataclass
from typing import Optional


@dataclass(frozen=True)
class DeliveryAddress:
    street: str
    street_number: str
    city: str
    province: str
    floor: Optional[str] = None
    apartment: Optional[str] = None
    postal_code: Optional[str] = None
