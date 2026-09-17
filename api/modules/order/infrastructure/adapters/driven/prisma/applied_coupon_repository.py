import uuid

from modules.order.application.ports.driven.applied_coupon_repository import (
    AppliedCouponRepositoryPort,
    AppliedCouponSnapshot,
)
from shared.infrastructure.prisma.db import db


class PrismaAppliedCouponRepository(AppliedCouponRepositoryPort):
    def __init__(self, client=None) -> None:
        # Accepts a transaction client so a coupon application can be recorded
        # in the same transaction as the order mutation.
        self._client = client if client is not None else db.client

    def add(self, snapshot: AppliedCouponSnapshot) -> AppliedCouponSnapshot:
        record_id = snapshot.id or str(uuid.uuid4())
        self._client.appliedcoupon.create(
            data={
                "id": record_id,
                "orderId": snapshot.order_id,
                "couponId": snapshot.coupon_id,
                "couponCode": snapshot.coupon_code,
                "type": snapshot.coupon_type,
                "amount": snapshot.amount,
                "discountAmount": snapshot.discount_amount,
                "availableUses": snapshot.available_uses,
                "dateOfExpiration": snapshot.date_of_expiration,
                "appliedAt": snapshot.applied_at,
            }
        )
        snapshot.id = record_id
        return snapshot

    def list_by_coupon(self, coupon_id: str) -> list[AppliedCouponSnapshot]:
        records = self._client.appliedcoupon.find_many(
            where={"couponId": coupon_id},
            order={"appliedAt": "desc"},
        )
        return [
            AppliedCouponSnapshot(
                id=r.id,
                order_id=r.orderId,
                coupon_id=r.couponId,
                coupon_code=r.couponCode,
                coupon_type=r.type,
                amount=r.amount,
                discount_amount=r.discountAmount,
                available_uses=r.availableUses,
                date_of_expiration=r.dateOfExpiration,
                applied_at=r.appliedAt,
            )
            for r in records
        ]
