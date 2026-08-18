from typing import Optional

from prisma import enums
from shared.infrastructure.prisma.db import db

from modules.order.application.ports.driven.order_repository import OrderRepository
from modules.order.domain.models.delivery_type import DeliveryType
from modules.order.domain.models.order import Order
from modules.order.domain.models.order_line import OrderLine
from modules.order.domain.models.order_state import OrderState
from modules.order.domain.models.payment_method import PaymentMethod


class PrismaOrderRepository(OrderRepository):
    def save(self, order: Order) -> Order:
        with db.client.tx() as tx:
            tx.order.upsert(
                where={"id": order.id},
                data={
                    "create": _to_prisma_data(order),
                    "update": _to_prisma_data(order),
                },
            )
            _sync_lines(tx, order)
        return order

    def get_by_id(self, order_id: str) -> Optional[Order]:
        record = db.client.order.find_first(
            where={"id": order_id},
            include={"lines": True},
        )
        if record is None:
            return None
        return _to_domain(record)


def _to_prisma_data(order: Order) -> dict:
    return {
        "id": order.id,
        "status": enums.OrderStatus(order.status.value),
        "subtotal": order.subtotal,
        "discount": order.discount,
        "clientId": order.client_id,
        "addressId": order.address_id,
        "conversationId": order.conversation_id,
        "estimatedTime": order.estimated_time,
        "deliveryType": _to_prisma_enum(enums.DeliveryType, order.delivery_type),
        "paymentType": _to_prisma_enum(enums.PaymentType, order.payment_type),
        "shippingCost": order.shipping_cost,
        "totalAmount": order.total_amount,
        "appliedCouponId": order.applied_coupon_id,
        "confirmedAt": order.confirmed_at,
    }


def _to_prisma_enum(enum_cls, value) -> Optional[str]:
    return enum_cls(value.value) if value is not None else None


def _sync_lines(tx, order: Order) -> None:
    line_ids = [line.id for line in order.lines]
    where = {"orderId": order.id}
    if line_ids:
        where["id"] = {"notIn": line_ids}
    tx.orderline.delete_many(where=where)

    for line in order.lines:
        tx.orderline.upsert(
            where={"id": line.id},
            data={
                "create": {
                    "id": line.id,
                    "orderId": order.id,
                    "productId": line.product_id,
                    "quantity": line.quantity,
                    "unitPrice": line.unit_price,
                    "subtotal": line.subtotal,
                    "discountId": line.discount_id,
                },
                "update": {
                    "quantity": line.quantity,
                    "unitPrice": line.unit_price,
                    "subtotal": line.subtotal,
                    "discountId": line.discount_id,
                },
            },
        )


def _to_domain(record) -> Order:
    lines = [
        OrderLine(
            id=line.id,
            order_id=record.id,
            product_id=line.productId,
            quantity=line.quantity,
            unit_price=line.unitPrice,
            subtotal=line.subtotal,
            discount_id=line.discountId,
        )
        for line in record.lines
    ]
    return Order(
        id=record.id,
        status=OrderState(record.status.value),
        subtotal=record.subtotal,
        discount=record.discount,
        client_id=record.clientId,
        address_id=record.addressId,
        conversation_id=record.conversationId,
        estimated_time=record.estimatedTime,
        delivery_type=DeliveryType(record.deliveryType.value) if record.deliveryType else None,
        payment_type=PaymentMethod(record.paymentType.value) if record.paymentType else None,
        shipping_cost=record.shippingCost,
        total_amount=record.totalAmount,
        applied_coupon_id=record.appliedCouponId,
        confirmed_at=record.confirmedAt,
        created_at=record.createdAt,
        lines=lines,
    )