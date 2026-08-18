from typing import Optional
from modules.order.application.ports.driven.order_repository import OrderRepository
from modules.order.domain.models.order import Order
from .models import OrderModel, OrderLineModel
from .mappers.order_mapper import OrderMapper


class DjangoOrderRepository(OrderRepository):
    def save(self, order: Order) -> Order:
        # Save order using mapper
        order_instance, _ = OrderModel.objects.update_or_create(
            id=order.id,
            defaults=OrderMapper.to_orm_defaults(order)
        )

        # Sync lines
        existing_line_ids = [line.id for line in order.lines]
        OrderLineModel.objects.filter(order=order_instance).exclude(id__in=existing_line_ids).delete()

        for line in order.lines:
            OrderLineModel.objects.update_or_create(
                id=line.id,
                defaults={
                    'order': order_instance,
                    'product_id': line.product_id,
                    'amount': line.quantity,
                    'unit_price': line.unit_price,
                    'subtotal': line.subtotal,
                    'discount_id': line.discount_id,
                }
            )

        return order

    def get_by_id(self, order_id: str) -> Optional[Order]:
        try:
            model = OrderModel.objects.prefetch_related('lines').get(id=order_id)
            return OrderMapper.to_domain(model)
        except OrderModel.DoesNotExist:
            return None
