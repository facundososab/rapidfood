"""PrismaCouponRepository — Prisma adapter implementing CouponRepositoryPort.

Data layer is owned by Prisma (single source of truth: schema.prisma). This
adapter maps between the Prisma ``Coupon`` model and the domain ``Coupon``
entity. All row<->entity mapping stays in this adapter.

The Prisma client instance is injected via the constructor at the composition
root (it is never a global here). It uses the shared ``db`` singleton from
``shared.infrastructure.prisma.db`` passed in by the caller.
"""

from __future__ import annotations

from prisma import Prisma

from modules.config_coupon.application.ports.driven.coupon_repository_port import (
    CouponRepositoryPort,
)
from modules.config_coupon.domain.models.coupon import Coupon
from modules.config_coupon.domain.models.coupon_code import CouponCode
from modules.config_coupon.domain.models.coupon_type import CouponType


class PrismaCouponRepository(CouponRepositoryPort):
    def __init__(self, prisma_client: Prisma) -> None:
        self._prisma = prisma_client

    def save(self, coupon: Coupon) -> Coupon:
        if coupon.coupon_id is None:
            return self._insert(coupon)
        return self._update(coupon)

    def find_by_code(self, coupon_code: str) -> Coupon | None:
        row = self._prisma.coupon.find_first(
            where={"couponCode": coupon_code},
        )
        return self._to_domain(row) if row is not None else None

    def find_by_id(self, coupon_id: str) -> Coupon | None:
        row = self._prisma.coupon.find_first(where={"id": coupon_id})
        return self._to_domain(row) if row is not None else None

    def list_all(self) -> list[Coupon]:
        rows = self._prisma.coupon.find_many(order={"couponCode": "asc"})
        return [self._to_domain(row) for row in rows]

    # --- persistence helpers -------------------------------------------------

    def _insert(self, coupon: Coupon) -> Coupon:
        row = self._prisma.coupon.create({**_data(coupon)})
        return self._to_domain(row)

    def _update(self, coupon: Coupon) -> Coupon:
        coupon_id = coupon.coupon_id
        if coupon_id is None:
            raise ValueError("Cannot update a coupon without a coupon_id")
        row = self._prisma.coupon.update(
            where={"id": coupon_id},
            data={**_data(coupon)},
        )
        return self._to_domain(row)

    @staticmethod
    def _to_domain(row: object) -> Coupon:  # type: ignore[type-arg]
        return Coupon(
            coupon_id=str(row.id),
            coupon_code=CouponCode(row.coupon_code),
            coupon_type=CouponType.from_value(row.type),
            amount=row.amount,
            min_order_amount=row.min_order_amount,
            available_uses=row.available_uses,
            date_of_expiration=row.date_of_expiration,
            is_active=row.is_active,
        )


def _data(coupon: Coupon) -> dict[str, object]:
    """Map the domain aggregate to a Prisma create/update data dict.

    Uses the Prisma schema FIELD names (camelCase); ``@map`` only affects the
    database column names, not the client field names.
    """
    data: dict[str, object] = {
        "couponCode": coupon.coupon_code.value,
        "type": coupon.coupon_type.value,
        "amount": coupon.amount,
        "availableUses": coupon.available_uses,
        "isActive": coupon.is_active,
    }
    if coupon.min_order_amount is not None:
        data["minOrderAmount"] = coupon.min_order_amount
    if coupon.date_of_expiration is not None:
        data["dateOfExpiration"] = coupon.date_of_expiration
    return data