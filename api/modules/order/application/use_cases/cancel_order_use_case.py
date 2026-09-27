from modules.order.application.ports.driver.cancel_order_ports import (
    CancelOrderCommand, CancelOrderResponse
)
from modules.order.application.ports.driven.order_repository import OrderRepository
from modules.order.domain.errors.order_errors import OrderNotFound, OrderNotModifiableError
from modules.order.domain.models.order_state import OrderState
from modules.order.domain.services.state_transitions import (
    CANCELLABLE_STATES,
    is_cancellable,
)


class CancelOrderUseCase:
    def __init__(self, order_repo: OrderRepository):
        self.order_repo = order_repo

    def execute(self, command: CancelOrderCommand) -> CancelOrderResponse:
        order = self.order_repo.get_by_id(command.order_id)
        if not order:
            raise OrderNotFound(f"Order {command.order_id} not found")

        # Idempotent retry: an already-cancelled order is a successful no-op.
        if order.status is OrderState.CANCELLED:
            return CancelOrderResponse(order_id=order.id, status=order.status.value)

        if not is_cancellable(order.status):
            raise OrderNotModifiableError(
                f"Cannot cancel an order in state {order.status.value}. "
                f"Cancellable states: {sorted(s.value for s in CANCELLABLE_STATES)}"
            )

        order.status = OrderState.CANCELLED
        self.order_repo.save(order)

        return CancelOrderResponse(
            order_id=order.id,
            status=order.status.value
        )
