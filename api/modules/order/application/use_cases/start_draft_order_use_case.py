from datetime import datetime
import uuid
from decimal import Decimal

from modules.order.application.ports.driver.start_draft_order_ports import (
    StartDraftOrderPort, StartDraftOrderCommand, StartDraftOrderResponse
)
from modules.order.application.ports.driven.order_repository import OrderRepository
from modules.order.application.ports.driven.client_query import ClientQuery
from modules.order.domain.models.order import Order
from modules.order.domain.models.order_state import OrderState
from modules.order.domain.models.order_origin import OrderOrigin


class StartDraftOrderUseCase(StartDraftOrderPort):
    def __init__(self, order_repo: OrderRepository, client_query: ClientQuery):
        self.order_repo = order_repo
        self.client_query = client_query

    def execute(self, command: StartDraftOrderCommand) -> StartDraftOrderResponse:
        if command.client_id:
            if not self.client_query.check_client_exists(command.client_id):
                raise ValueError("Client does not exist")

        order = Order(
            id=str(uuid.uuid4()),
            status=OrderState.DRAFT,
            subtotal=Decimal("0.0"),
            discount=Decimal("0.0"),
            client_id=command.client_id,
            conversation_id=command.conversation_id,
            origin=OrderOrigin(command.origin) if command.origin else OrderOrigin.IN_PLACE,
            created_at=datetime.utcnow()
        )
        
        self.order_repo.save(order)
        
        return StartDraftOrderResponse(
            order_id=order.id,
            status=order.status.value
        )
