"""Attach the customer's name (and optional registered client) to a draft order.

Only meaningful while the order is a DRAFT: the customer identity must be known
BEFORE the summary is confirmed, never after.
"""
from __future__ import annotations

from modules.order.application.ports.driven.client_query import ClientQuery
from modules.order.application.ports.driven.order_repository import OrderRepository
from modules.order.application.ports.driver.set_client_for_order_port import (
    SetClientForOrderCommand,
    SetClientForOrderPort,
    SetClientForOrderResponse,
)
from modules.order.domain.errors.order_errors import (
    OrderNotFound,
    OrderNotModifiableError,
)
from modules.order.domain.models.order_state import OrderState


class SetClientForOrderUseCase(SetClientForOrderPort):
    def __init__(self, order_repo: OrderRepository, client_query: ClientQuery) -> None:
        self.order_repo = order_repo
        self.client_query = client_query

    def execute(self, command: SetClientForOrderCommand) -> SetClientForOrderResponse:
        order = self.order_repo.get_by_id(command.order_id)
        if order is None:
            raise OrderNotFound("Order not found")

        if order.status is not OrderState.DRAFT:
            raise OrderNotModifiableError(
                "The client can only be set while the order is a draft"
            )

        client_name = (command.client_name or "").strip() or None
        if client_name:
            order.client_name = client_name

        if command.client_id:
            if not self.client_query.check_client_exists(command.client_id):
                raise OrderNotFound(f"Client {command.client_id} not found")
            order.client_id = command.client_id

        self.order_repo.save(order)

        return SetClientForOrderResponse(
            order_id=order.id,
            client_id=order.client_id,
            client_name=order.client_name,
        )
