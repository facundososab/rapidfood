from typing import Dict, Any
from decimal import Decimal
from modules.order.domain.models.order import Order
from modules.order.domain.models.order_line import OrderLine
from modules.order.domain.models.order_state import OrderState
from modules.order.domain.models.delivery_type import DeliveryType
from modules.order.domain.models.payment_method import PaymentMethod
from modules.order.infrastructure.adapters.driven.django_orm.models import OrderModel


class OrderMapper:
    @staticmethod
    def to_domain(model: OrderModel) -> Order:
        """Translates Django ORM Model to Domain Entity."""
        delivery_type = None
        if model.delivery_type:
            try:
                delivery_type = DeliveryType(model.delivery_type)
            except ValueError:
                pass

        payment_type = None
        if model.payment_type:
            try:
                payment_type = PaymentMethod(model.payment_type)
            except ValueError:
                pass

        lines = [
            OrderLine(
                id=str(line_model.id),
                order_id=str(model.id),
                product_id=str(line_model.product_id),
                quantity=line_model.amount,
                unit_price=Decimal(line_model.unit_price) if line_model.unit_price else None,
                subtotal=Decimal(line_model.subtotal),
                discount_id=str(line_model.discount_id) if line_model.discount_id else None
            ) for line_model in model.lines.all()
        ]

        order = Order(
            id=str(model.id),
            status=OrderState(model.status),
            subtotal=Decimal("0.0"),  # Recalculated below
            discount=Decimal("0.0"),
            client_id=str(model.client_id) if model.client_id else None,
            conversation_id=str(model.conversation_id) if model.conversation_id else None,
            estimated_time=model.estimated_time,
            delivery_type=delivery_type,
            payment_type=payment_type,
            shipping_cost=Decimal(model.shipping_cost) if model.shipping_cost else Decimal("0.0"),
            total_amount=Decimal(model.total_amount) if model.total_amount else Decimal("0.0"),
            address_id=str(model.address_id) if model.address_id else None,
            lines=lines
        )
        order._recalculate_totals()
        return order

    @staticmethod
    def to_orm_defaults(order: Order) -> Dict[str, Any]:
        """Translates Domain Entity to kwargs for update_or_create."""
        return {
            'status': order.status.value,
            'client_id': order.client_id,
            'conversation_id': order.conversation_id,
            'estimated_time': order.estimated_time,
            'delivery_type': order.delivery_type.value if order.delivery_type else None,
            'payment_type': order.payment_type.value if order.payment_type else None,
            'shipping_cost': order.shipping_cost,
            'total_amount': order.total_amount,
            'address_id': order.address_id,
        }
