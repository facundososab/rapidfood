import uuid

from modules.order.application.ports.driven.applied_coupon_repository import (
    AppliedCouponRepositoryPort,
    AppliedCouponSnapshot,
)
from shared.infrastructure.prisma.db import db


class PrismaAppliedCouponRepository(AppliedCouponRepositoryPort):
    def add(self, snapshot: AppliedCouponSnapshot) -> AppliedCouponSnapshot:
        record_id = snapshot.id or str(uuid.uuid4())
        db.client.appliedcoupon.create(
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
        records = db.client.appliedcoupon.find_many(
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
