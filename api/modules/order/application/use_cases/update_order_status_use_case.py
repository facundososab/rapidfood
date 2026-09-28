from modules.order.application.ports.driver.update_order_status_ports import (
    UpdateOrderStatusCommand,
    UpdateOrderStatusPort,
    UpdateOrderStatusResponse,
)
from modules.order.application.ports.driven.order_repository import OrderRepository
from modules.order.domain.errors.order_errors import OrderNotFound, OrderStateError
from modules.order.domain.models.order_state import OrderState
from modules.order.domain.services.state_transitions import (
    allowed_transitions,
    can_transition,
)


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

        if not can_transition(order.status, target, order.payment_type):
            allowed = allowed_transitions(order.status, order.payment_type)
            raise OrderStateError(
                f"Cannot transition from {order.status.value} to {target.value}. "
                f"Allowed: {[s.value for s in allowed]}"
            )

        order.status = target
        self.order_repo.save(order)

        return UpdateOrderStatusResponse(order_id=order.id, status=order.status.value)