"""Reopen-aware, idempotent set-delivery use case.

The delivery quote is an external computation (geocoding + routing + pricing
owned by the ``delivery`` context), so it is resolved BEFORE the transaction. If
the address is not deliverable the order is not touched at all. Only the
resulting snapshot (address + quoted shipping cost) is written inside the
mutation transaction.
"""
from __future__ import annotations

from typing import Optional

from modules.order.application.idempotency_key import build_idempotency_key
from modules.order.application.order_modification import prepare_order_for_modification
from modules.order.application.ports.driven.clock import ClockPort
from modules.order.application.ports.driven.delivery_quote_query import DeliveryQuoteQuery
from modules.order.application.ports.driven.idempotency import (
    IdempotentOrderMutationPort,
    OrderMutationContext,
)
from modules.order.application.ports.driver.set_delivery_for_order_port import (
    SetDeliveryForOrderCommand,
    SetDeliveryForOrderPort,
    SetDeliveryForOrderResponse,
)
from modules.order.domain.errors.order_errors import (
    DeliveryAddressRequiredError,
    DeliveryNotAvailableError,
)
from modules.order.domain.models.delivery_address import DeliveryAddress
from modules.order.domain.models.delivery_type import DeliveryType

_OPERATION_NAME = "set_delivery"


class SetDeliveryForOrderUseCase(SetDeliveryForOrderPort):
    def __init__(
        self,
        delivery_quote: DeliveryQuoteQuery,
        executor: IdempotentOrderMutationPort,
        clock: ClockPort,
        prep_time_estimator: Optional[object] = None,
    ) -> None:
        self._delivery_quote = delivery_quote
        self._executor = executor
        self._clock = clock
        self._prep_time_estimator = prep_time_estimator

    def execute(self, command: SetDeliveryForOrderCommand) -> SetDeliveryForOrderResponse:
        destination = _destination_from(command)

        # May raise DeliveryNotAvailableError (business) or DeliveryQuoteFailedError
        # (technical) — never silently treated as "outside the zone".
        quote = self._delivery_quote.quote(command.business_config_id, destination)
        if not quote.available or quote.shipping_cost is None:
            raise DeliveryNotAvailableError("No se puede entregar en esa dirección.")

        route_duration = (
            round(quote.estimated_duration_minutes)
            if quote.estimated_duration_minutes is not None
            else None
        )
        estimated_time = self._estimate_time(
            command.business_config_id, route_duration
        )

        idempotency_key = build_idempotency_key(
            business_config_id=command.business_config_id,
            conversation_id=command.conversation_id,
            external_message_id=command.external_message_id,
            operation_name=_OPERATION_NAME,
            args={
                "order_id": command.order_id,
                "street": destination.street,
                "street_number": destination.street_number,
                "floor": destination.floor,
                "apartment": destination.apartment,
                "city": destination.city,
                "province": destination.province,
                "postal_code": destination.postal_code,
            },
        )

        def mutate(ctx: OrderMutationContext) -> dict:
            order = ctx.order
            ctx.superseded_attempt_ids.extend(
                prepare_order_for_modification(order, ctx.attempts, self._clock.now())
            )

            order.delivery_type = DeliveryType.DELIVERY
            order.delivery_address = destination
            order.shipping_cost = quote.shipping_cost
            order.business_config_id = command.business_config_id
            order.route_duration_minutes = route_duration
            order.estimated_time = estimated_time
            order.mark_modified()

            return {
                "order_id": order.id,
                "shipping_cost": str(order.shipping_cost),
                "total_amount": str(order.total_amount),
                "version": order.version,
            }

        outcome = self._executor.execute(
            business_config_id=command.business_config_id,
            idempotency_key=idempotency_key,
            operation_name=_OPERATION_NAME,
            order_id=command.order_id,
            mutate=mutate,
        )

        return SetDeliveryForOrderResponse(
            replayed=outcome.replayed,
            superseded_attempt_ids=outcome.superseded_attempt_ids,
            **outcome.result,
        )

    def _estimate_time(self, business_config_id: str, route_duration) -> Optional[int]:
        """ETA = preparation (demand) + delivery travel time, when available."""
        if self._prep_time_estimator is None:
            return None
        prep = self._prep_time_estimator.estimate_minutes(business_config_id)
        return prep + (route_duration or 0)


def _destination_from(command: SetDeliveryForOrderCommand) -> DeliveryAddress:
    street = (command.street or "").strip()
    street_number = (command.street_number or "").strip()
    city = (command.city or "").strip()
    province = (command.province or "").strip()
    if not (street and street_number and city and province):
        raise DeliveryAddressRequiredError(
            "Completá calle, número, ciudad y provincia para el envío."
        )
    return DeliveryAddress(
        street=street,
        street_number=street_number,
        city=city,
        province=province,
        floor=(command.floor or "").strip() or None,
        apartment=(command.apartment or "").strip() or None,
        postal_code=(command.postal_code or "").strip() or None,
    )
