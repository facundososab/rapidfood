"""Adapts the delivery module's quote use case to the order module's port.

Cross-context boundary: delivery errors (not configured, geocoding/routing
failure) are not importable here, so they are translated into an order-domain
error that the REST edge can surface as a friendly message.
"""
from __future__ import annotations

from typing import Any

from modules.delivery.application.ports.driver.calculate_delivery_quote_ports import (
    AddressInput,
    CalculateDeliveryQuoteCommand,
)
from modules.order.application.ports.driven.delivery_quote_query import (
    DeliveryQuoteQuery,
    DeliveryQuoteSnapshot,
)
from modules.order.domain.errors.order_errors import DeliveryQuoteFailedError
from modules.order.domain.models.delivery_address import DeliveryAddress


class DeliveryQuoteAdapter(DeliveryQuoteQuery):
    def __init__(self, calculate_delivery_quote: Any) -> None:
        self._calculate_delivery_quote = calculate_delivery_quote

    def quote(
        self, business_config_id: str, destination: DeliveryAddress
    ) -> DeliveryQuoteSnapshot:
        try:
            result = self._calculate_delivery_quote.execute(
                CalculateDeliveryQuoteCommand(
                    business_config_id=business_config_id,
                    destination_address=AddressInput(
                        street=destination.street,
                        street_number=destination.street_number,
                        city=destination.city,
                        province=destination.province,
                        floor=destination.floor,
                        apartment=destination.apartment,
                        postal_code=destination.postal_code,
                    ),
                )
            )
        except Exception as exc:
            raise DeliveryQuoteFailedError(str(exc)) from exc

        return DeliveryQuoteSnapshot(
            available=result.available,
            shipping_cost=result.shipping_cost,
            distance_km=result.distance_km,
            estimated_duration_minutes=result.estimated_duration_minutes,
            demand_level=result.demand_level,
        )
