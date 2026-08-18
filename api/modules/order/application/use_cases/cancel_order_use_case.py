from modules.order.application.ports.driver.cancel_order_ports import (
    CancelOrderCommand, CancelOrderResponse
)
from modules.order.application.ports.driven.order_repository import OrderRepository
from modules.order.domain.errors.order_errors import OrderNotFound, OrderNotModifiableError
from modules.order.domain.models.order_state import OrderState


# These states allow cancellation
_CANCELLABLE_STATES = {OrderState.DRAFT, OrderState.PENDING, OrderState.PAID}


class CancelOrderUseCase:
    def __init__(self, order_repo: OrderRepository):
        self.order_repo = order_repo

    def execute(self, command: CancelOrderCommand) -> CancelOrderResponse:
        order = self.order_repo.get_by_id(command.order_id)
        if not order:
            raise OrderNotFound(f"Order {command.order_id} not found")

        if order.status not in _CANCELLABLE_STATES:
            raise OrderNotModifiableError(
                f"Cannot cancel an order in state {order.status.value}. "
                f"Cancellable states: {[s.value for s in _CANCELLABLE_STATES]}"
            )

        order.status = OrderState.CANCELLED
        self.order_repo.save(order)

        return CancelOrderResponse(
            order_id=order.id,
            status=order.status.value
        )
