"""Adapts the delivery module's quote port to `DeliveryServicePort`.

Reuses the EXISTING delivery quote capability — no second pricing engine. The
delivery module owns geocoding, zone validation, routing, demand and pricing;
conversation only receives the resulting quote.
"""
from __future__ import annotations

from typing import Any

from modules.conversation.application.ports.driven.delivery_service import (
    DeliveryQuoteDTO,
    DeliveryServicePort,
)
from modules.delivery.application.ports.driver.calculate_delivery_quote_ports import (
    AddressInput,
    CalculateDeliveryQuoteCommand,
)


class DeliveryServiceAdapter(DeliveryServicePort):
    def __init__(self, calculate_delivery_quote: Any) -> None:
        self._calculate_delivery_quote = calculate_delivery_quote

    def quote_delivery(
        self, business_configuration_id: str, destination_address: dict
    ) -> DeliveryQuoteDTO:
        result = self._calculate_delivery_quote.execute(
            CalculateDeliveryQuoteCommand(
                business_config_id=business_configuration_id,
                destination_address=AddressInput(
                    street=destination_address.get("street", ""),
                    street_number=destination_address.get("street_number", ""),
                    city=destination_address.get("city", ""),
                    province=destination_address.get("province", ""),
                    floor=destination_address.get("floor"),
                    apartment=destination_address.get("apartment"),
                    postal_code=destination_address.get("postal_code"),
                ),
            )
        )
        return DeliveryQuoteDTO(
            available=result.available,
            shipping_cost=(
                str(result.shipping_cost) if result.shipping_cost is not None else None
            ),
            distance_km=result.distance_km,
            estimated_duration_minutes=result.estimated_duration_minutes,
            demand_level=result.demand_level,
        )
