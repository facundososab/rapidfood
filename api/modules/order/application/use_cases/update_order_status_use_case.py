from modules.order.application.ports.driver.update_order_status_ports import (
    UpdateOrderStatusCommand,
    UpdateOrderStatusPort,
    UpdateOrderStatusResponse,
)
from modules.order.application.ports.driven.order_repository import OrderRepository
from modules.order.domain.errors.order_errors import OrderNotFound, OrderStateError
from modules.order.domain.models.order_state import OrderState

# Forward + cancellation transitions accepted by the admin panel. Cancelling a
# terminal order (DELIVERED/PICKED_UP/CANCELLED) is not allowed.
_ALLOWED_TRANSITIONS: dict[OrderState, set[OrderState]] = {
    OrderState.DRAFT: {OrderState.PENDING, OrderState.CANCELLED},
    OrderState.PENDING: {OrderState.PAID, OrderState.CANCELLED},
    OrderState.PAID: {OrderState.CONFIRMED, OrderState.CANCELLED},
    OrderState.CONFIRMED: {OrderState.IN_PREPARATION, OrderState.CANCELLED},
    OrderState.IN_PREPARATION: {OrderState.READY, OrderState.CANCELLED},
    OrderState.READY: {OrderState.DELIVERED, OrderState.PICKED_UP, OrderState.CANCELLED},
    OrderState.DELIVERED: set(),
    OrderState.PICKED_UP: set(),
    OrderState.CANCELLED: set(),
}


class UpdateOrderStatusUseCase(UpdateOrderStatusPort):
    def __init__(self, order_repo: OrderRepository):
        self.order_repo = order_repo

    def execute(self, command: UpdateOrderStatusCommand) -> UpdateOrderStatusResponse:
        order = self.order_repo.get_by_id(command.order_id)
        if order is None:
            raise OrderNotFound(f"Order {command.order_id} not found")

        try:
            target = OrderState(command.status)
        except ValueError:
            raise OrderStateError(f"'{command.status}' is not a valid order state")

        if target == order.status:
            return UpdateOrderStatusResponse(order_id=order.id, status=order.status.value)

        allowed = _ALLOWED_TRANSITIONS.get(order.status, set())
        if target not in allowed:
            raise OrderStateError(
                f"Cannot transition from {order.status.value} to {target.value}. "
                f"Allowed: {[s.value for s in allowed]}"
            )

        order.status = target
        self.order_repo.save(order)

        return UpdateOrderStatusResponse(order_id=order.id, status=order.status.value)