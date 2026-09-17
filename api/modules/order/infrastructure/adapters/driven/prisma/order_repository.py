import uuid
from typing import List, Optional

from prisma import enums
from shared.infrastructure.prisma.db import db

from modules.order.application.ports.driven.order_repository import (
    OrderFilter,
    OrderRepository,
)
from modules.order.domain.models.delivery_type import DeliveryType
from modules.order.domain.models.order import Order
from modules.order.domain.models.order_line import OrderLine
from modules.order.domain.models.order_line_modifier import OrderLineModifier
from modules.order.domain.models.order_line_removed_ingredient import OrderLineRemovedIngredient
from modules.order.domain.models.delivery_address import DeliveryAddress
from modules.order.domain.models.order_origin import OrderOrigin
from modules.order.domain.models.order_state import OrderState
from modules.order.domain.models.payment_method import PaymentMethod
from decimal import Decimal


class PrismaOrderRepository(OrderRepository):
    def save(self, order: Order) -> Order:
        with db.client.tx() as tx:
            persist_order_in_tx(tx, order)
        return order

    def get_by_id(self, order_id: str) -> Optional[Order]:
        return load_order_in_tx(db.client, order_id)

    def list(self, filter: Optional[OrderFilter] = None) -> List[Order]:
        filter = filter or OrderFilter()
        where: dict = {}
        if filter.status is not None:
            where["status"] = enums.OrderStatus(filter.status.value)
        if filter.status_in is not None:
            where["status"] = {"in": [enums.OrderStatus(s.value) for s in filter.status_in]}
        if filter.exclude_status_in is not None:
            where["status"] = {
                "notIn": [enums.OrderStatus(s.value) for s in filter.exclude_status_in]
            }
        if filter.delivery_type is not None:
            where["deliveryType"] = enums.DeliveryType(filter.delivery_type.value)
        if filter.payment_type is not None:
            where["paymentType"] = enums.PaymentType(filter.payment_type.value)
        if filter.conversation_id is not None:
            where["conversationId"] = filter.conversation_id
        if filter.business_config_id is not None:
            where["businessConfigId"] = filter.business_config_id
        if filter.client_id is not None:
            where["clientId"] = filter.client_id
        created_at: dict = {}
        if filter.date_from is not None:
            created_at["gte"] = filter.date_from
        if filter.date_to is not None:
            created_at["lte"] = filter.date_to
        if created_at:
            where["createdAt"] = created_at

        records = db.client.order.find_many(
            where=where,
            order={"createdAt": "desc"},
            include=_ORDER_INCLUDE,
        )
        return [_to_domain(record) for record in records]


_ORDER_INCLUDE = {
    "lines": {"include": {"modifiers": True, "removedIngredients": True}}
}


def persist_order_in_tx(tx, order: Order) -> None:
    """Persist an order aggregate (scalars + lines + children) inside a tx."""
    tx.order.upsert(
        where={"id": order.id},
        data={
            "create": _to_prisma_data(order),
            "update": _to_prisma_data(order),
        },
    )
    _sync_lines(tx, order)


def load_order_in_tx(tx, order_id: str) -> Optional[Order]:
    """Load a full order aggregate inside a tx (or from the base client)."""
    record = tx.order.find_first(where={"id": order_id}, include=_ORDER_INCLUDE)
    if record is None:
        return None
    return _to_domain(record)


def _to_prisma_data(order: Order) -> dict:
    return {
        "id": order.id,
        "status": enums.OrderStatus(order.status.value),
        "origin": enums.OrderOrigin(order.origin.value),
        "subtotal": order.subtotal,
        "discount": order.discount,
        "version": order.version,
        "clientId": _id(order.client_id),
        "clientName": order.client_name,
        "businessConfigId": _id(order.business_config_id),
        "addressId": _id(order.address_id),
        "conversationId": _id(order.conversation_id),
        "estimatedTime": order.estimated_time,
        "deliveryType": _to_prisma_enum(enums.DeliveryType, order.delivery_type),
        "paymentType": _to_prisma_enum(enums.PaymentType, order.payment_type),
        "shippingCost": order.shipping_cost,
        "totalAmount": order.total_amount,
        "appliedCouponId": _id(order.applied_coupon_id),
        "couponCode": order.coupon_code,
        "deliveryStreet": _da(order, "street"),
        "deliveryStreetNumber": _da(order, "street_number"),
        "deliveryFloor": _da(order, "floor"),
        "deliveryApartment": _da(order, "apartment"),
        "deliveryCity": _da(order, "city"),
        "deliveryProvince": _da(order, "province"),
        "deliveryPostalCode": _da(order, "postal_code"),
        "confirmedAt": order.confirmed_at,
    }


def _da(order: Order, field: str):
    return getattr(order.delivery_address, field) if order.delivery_address else None


def _id(value):
    """Normalize ids to str (Prisma can't serialize uuid.UUID objects)."""
    return str(value) if value else None


def _to_prisma_enum(enum_cls, value) -> Optional[str]:
    return enum_cls(value.value) if value is not None else None


def _sync_lines(tx, order: Order) -> None:
    """Sync order lines and their children within an active transaction."""
    line_ids = [line.id for line in order.lines]
    where = {"orderId": order.id}
    if line_ids:
        where["id"] = {"notIn": line_ids}
    # Delete lines that are no longer in the order (cascades to modifiers + removed_ingredients)
    tx.orderline.delete_many(where=where)

    for line in order.lines:
        tx.orderline.upsert(
            where={"id": line.id},
            data={
                "create": {
                    "id": line.id,
                    "orderId": order.id,
                    "productVariantId": line.product_variant_id,
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

        # Sync OrderLineModifier children
        existing_modifier_ids = [m.id for m in line.modifiers]
        modifier_where = {"orderLineId": line.id}
        if existing_modifier_ids:
            modifier_where["id"] = {"notIn": existing_modifier_ids}
        tx.orderlinemodifier.delete_many(where=modifier_where)
        for modifier in line.modifiers:
            tx.orderlinemodifier.upsert(
                where={"id": modifier.id},
                data={
                    "create": {
                        "id": modifier.id,
                        "orderLineId": line.id,
                        "modifierOptionId": modifier.modifier_option_id,
                        "optionNameSnapshot": modifier.option_name_snapshot,
                        "priceDelta": modifier.price_delta,
                    },
                    "update": {
                        "optionNameSnapshot": modifier.option_name_snapshot,
                        "priceDelta": modifier.price_delta,
                    },
                },
            )

        # Sync OrderLineRemovedIngredient children
        existing_removed_ids = [r.id for r in line.removed_ingredients]
        removed_where = {"orderLineId": line.id}
        if existing_removed_ids:
            removed_where["id"] = {"notIn": existing_removed_ids}
        tx.orderlineremovedingredient.delete_many(where=removed_where)
        for removed in line.removed_ingredients:
            tx.orderlineremovedingredient.upsert(
                where={"id": removed.id},
                data={
                    "create": {
                        "id": removed.id,
                        "orderLineId": line.id,
                        "ingredientId": removed.ingredient_id,
                        "ingredientNameSnapshot": removed.ingredient_name_snapshot,
                    },
                    "update": {
                        "ingredientNameSnapshot": removed.ingredient_name_snapshot,
                    },
                },
            )


def _to_domain(record) -> Order:
    lines = [_line_to_domain(line) for line in record.lines]
    return Order(
        id=record.id,
        status=OrderState(_enum_value(record.status)),
        subtotal=record.subtotal,
        discount=record.discount,
        version=record.version,
        client_id=record.clientId,
        client_name=record.clientName,
        business_config_id=record.businessConfigId,
        address_id=record.addressId,
        conversation_id=record.conversationId,
        estimated_time=record.estimatedTime,
        delivery_type=_optional_enum(DeliveryType, record.deliveryType),
        payment_type=_optional_enum(PaymentMethod, record.paymentType),
        origin=_optional_enum(OrderOrigin, record.origin) or OrderOrigin.IN_PLACE,
        shipping_cost=record.shippingCost,
        total_amount=record.totalAmount,
        applied_coupon_id=record.appliedCouponId,
        coupon_code=record.couponCode,
        delivery_address=_delivery_address(record),
        confirmed_at=record.confirmedAt,
        created_at=record.createdAt,
        lines=lines,
    )


def _delivery_address(record):
    if not record.deliveryStreet:
        return None
    return DeliveryAddress(
        street=record.deliveryStreet,
        street_number=record.deliveryStreetNumber or "",
        city=record.deliveryCity or "",
        province=record.deliveryProvince or "",
        floor=record.deliveryFloor,
        apartment=record.deliveryApartment,
        postal_code=record.deliveryPostalCode,
    )


def _line_to_domain(line) -> OrderLine:
    modifiers = [
        OrderLineModifier(
            id=m.id,
            order_line_id=line.id,
            modifier_option_id=m.modifierOptionId,
            option_name_snapshot=m.optionNameSnapshot,
            price_delta=Decimal(str(m.priceDelta)) if m.priceDelta is not None else None,
        )
        for m in (line.modifiers or [])
    ]
    removed_ingredients = [
        OrderLineRemovedIngredient(
            id=r.id,
            order_line_id=line.id,
            ingredient_id=r.ingredientId,
            ingredient_name_snapshot=r.ingredientNameSnapshot,
        )
        for r in (line.removedIngredients or [])
    ]
    return OrderLine(
        id=line.id,
        order_id=line.orderId,
        product_variant_id=line.productVariantId,
        quantity=line.quantity,
        unit_price=line.unitPrice,
        subtotal=line.subtotal,
        discount_id=line.discountId,
        modifiers=modifiers,
        removed_ingredients=removed_ingredients,
    )


def _enum_value(value) -> str:
    return value.value if hasattr(value, "value") else value


def _optional_enum(enum_cls, value):
    if value is None:
        return None
    return enum_cls(_enum_value(value))