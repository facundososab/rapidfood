"""Reliable order summary for the agent, including missing requirements.

Every amount comes from the order aggregate; the missing requirements reflect
real order rules so the agent knows what to ask before confirming. No duplicated
persistence is created for the summary.
"""
from __future__ import annotations

from decimal import Decimal

from modules.order.application.ports.driven.business_config_query import (
    BusinessConfigQueryPort,
)
from modules.order.application.ports.driven.order_repository import OrderRepository
from modules.order.application.ports.driver.get_order_summary_port import (
    GetOrderSummaryPort,
    OrderSummaryDTO,
    OrderSummaryLineDTO,
)
from modules.order.domain.errors.order_errors import OrderNotFound
from modules.order.domain.models.delivery_type import DeliveryType


class GetOrderSummaryUseCase(GetOrderSummaryPort):
    def __init__(
        self,
        order_repo: OrderRepository,
        config_query: BusinessConfigQueryPort,
    ) -> None:
        self._order_repo = order_repo
        self._config_query = config_query

    def execute(self, order_id: str) -> OrderSummaryDTO:
        order = self._order_repo.get_by_id(order_id)
        if order is None:
            raise OrderNotFound("Order not found")

        missing = self._missing_requirements(order)

        return OrderSummaryDTO(
            order_id=order.id,
            status=order.status.value,
            version=order.version,
            lines=[
                OrderSummaryLineDTO(
                    line_id=line.id,
                    product_variant_id=line.product_variant_id,
                    quantity=line.quantity,
                    unit_price=(
                        str(line.unit_price) if line.unit_price is not None else None
                    ),
                    subtotal=str(line.subtotal),
                    modifiers=[
                        {
                            "id": m.id,
                            "modifier_option_id": m.modifier_option_id,
                            "name": m.option_name_snapshot,
                            "price_delta": (
                                str(m.price_delta) if m.price_delta is not None else None
                            ),
                        }
                        for m in line.modifiers
                    ],
                    removed_ingredients=[
                        {
                            "id": r.id,
                            "ingredient_id": r.ingredient_id,
                            "name": r.ingredient_name_snapshot,
                        }
                        for r in line.removed_ingredients
                    ],
                )
                for line in order.lines
            ],
            subtotal=str(order.subtotal),
            discount=str(order.discount),
            shipping_cost=(
                str(order.shipping_cost) if order.shipping_cost is not None else None
            ),
            total_amount=(
                str(order.total_amount) if order.total_amount is not None else None
            ),
            delivery_type=(
                order.delivery_type.value if order.delivery_type is not None else None
            ),
            address=(
                {
                    "street": order.delivery_address.street,
                    "street_number": order.delivery_address.street_number,
                    "floor": order.delivery_address.floor,
                    "apartment": order.delivery_address.apartment,
                    "city": order.delivery_address.city,
                    "province": order.delivery_address.province,
                    "postal_code": order.delivery_address.postal_code,
                }
                if order.delivery_address is not None
                else None
            ),
            payment_type=(
                order.payment_type.value if order.payment_type is not None else None
            ),
            estimated_time=order.estimated_time,
            client_id=order.client_id,
            client_name=order.client_name,
            missing_requirements=missing,
        )

    def _missing_requirements(self, order) -> list[str]:
        missing: list[str] = []
        if not order.lines:
            missing.append("empty_order")
        if order.delivery_type is None:
            missing.append("delivery_type")
        elif order.delivery_type is DeliveryType.DELIVERY:
            if order.delivery_address is None:
                missing.append("delivery_address")
        if order.payment_type is None:
            missing.append("payment_type")
        if not (order.client_id or (order.client_name or "").strip()):
            missing.append("client")

        if order.delivery_type is DeliveryType.DELIVERY:
            config = self._config_query.get_config()
            minimum = Decimal(str(config.min_order_amount or 0))
            if minimum > 0 and order.subtotal < minimum:
                missing.append("minimum_order_not_reached")

        return missing
