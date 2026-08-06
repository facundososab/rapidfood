"""Coupon repository port (driven/outbound).

Application depends ONLY on this interface. The concrete implementation
(Prisma adapter) is injected at the composition root.
"""

from __future__ import annotations

from typing import Protocol

from modules.config_coupon.domain.models.coupon import Coupon


class CouponRepositoryPort(Protocol):
    """Persistence contract for the Coupon aggregate."""

    def save(self, coupon: Coupon) -> Coupon:
        """Persist the coupon (create or update) and return it with an id."""
        ...

    def find_by_code(self, coupon_code: str) -> Coupon | None:
        """Find a coupon by its normalized code, or None."""
        ...

    def find_by_id(self, coupon_id: str) -> Coupon | None:
        """Find a coupon by its persistence id, or None."""
        ...

    def list_all(self) -> list[Coupon]:
        """List all coupons (admin catalog)."""
        ...