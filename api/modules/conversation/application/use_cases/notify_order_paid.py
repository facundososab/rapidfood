"""Notify the customer, on their own channel, that an order was paid.

Triggered POST-COMMIT by the payment webhook (best effort). The confirmation is
composed from the order summary — the source of truth — and delivered through the
outbound channel port. This use case owns no channel detail: the destination and
the delivery mechanism belong to the adapter behind the port.
"""
from __future__ import annotations

from typing import Any
from uuid import uuid4

from modules.conversation.application.ports.driven.order_service import (
    OrderSummaryDTO,
)
from modules.conversation.application.ports.driven.outbound_message import (
    OutboundMessage,
    OutboundMessagePort,
)
from modules.conversation.application.ports.driven.clock import ClockPort
from modules.conversation.application.ports.driven.message_repository import (
    MessageRepositoryPort,
)
from modules.conversation.domain.models.message import Message
from modules.conversation.domain.value_objects import MessageRole, MessageStatus
from modules.conversation.application.ports.driver.notify_order_paid_port import (
    NotifyOrderPaidCommand,
    NotifyOrderPaidPort,
)

_PICKUP = "PICKUP"


class NotifyOrderPaidUseCase(NotifyOrderPaidPort):
    def __init__(
        self,
        order_service: Any,
        conversation_repository: Any,
        message_repository: MessageRepositoryPort,
        outbound_message: OutboundMessagePort,
        clock: ClockPort,
    ) -> None:
        self._order_service = order_service
        self._conversation_repository = conversation_repository
        self._message_repository = message_repository
        self._outbound = outbound_message
        self._clock = clock

    def execute(self, command: NotifyOrderPaidCommand) -> bool:
        conversation = self._conversation_repository.get_by_id(command.conversation_id)
        if conversation is None:
            return False

        summary = self._order_service.get_order_summary(command.order_id)
        content = compose_order_paid_message(summary)

        # Persist here: the outbound port is send-only, so the notification would
        # otherwise be missing from the panel thread.
        self._message_repository.add(
            Message(
                message_id=str(uuid4()),
                conversation_id=command.conversation_id,
                role=MessageRole.AGENT,
                content=content,
                status=MessageStatus.PROCESSED,
                created_at=self._clock.now(),
            )
        )
        self._outbound.send(
            OutboundMessage(
                conversation_id=command.conversation_id,
                channel=conversation.channel,
                destination=(
                    conversation.channel_identity or conversation.external_thread_id
                ),
                content=content,
            )
        )
        return True


def compose_order_paid_message(summary: OrderSummaryDTO) -> str:
    """Customer-facing confirmation: items, totals, delivery and ETA."""
    items = "\n".join(_line(line) for line in summary.lines) or "- (sin productos)"

    parts = [
        "¡Pago acreditado! Tu pedido quedó confirmado.",
        "",
        items,
        "",
        f"Subtotal: ${summary.subtotal}",
    ]
    if summary.discount and summary.discount not in ("0", "0.0", "0.00"):
        parts.append(f"Descuento: -${summary.discount}")
    if summary.shipping_cost:
        parts.append(f"Envío: ${summary.shipping_cost}")
    if summary.total_amount:
        parts.append(f"Total: ${summary.total_amount}")

    parts.append("")
    if summary.delivery_type == _PICKUP:
        parts.append("Retiro en el local")
    else:
        parts.append("Envío a domicilio")
        address = _format_address(summary.address)
        if address:
            parts.append(address)

    if summary.estimated_time:
        parts.append(f"Tiempo estimado: {summary.estimated_time} minutos")

    parts.extend(["", "¡Gracias por tu compra!"])
    return "\n".join(parts)


def _line(line) -> str:
    name = " ".join(
        part for part in [line.product_name, line.variant_name] if part
    ) or line.product_variant_id
    if line.unit_price:
        return f"- {line.quantity}× {name} (${line.unit_price} c/u)"
    return f"- {line.quantity}× {name}"


def _format_address(address) -> str:
    if not address:
        return ""
    street = address.get("street") or ""
    number = address.get("street_number") or ""
    city = address.get("city") or ""
    return " ".join(part for part in [f"{street} {number}".strip(), city] if part)
