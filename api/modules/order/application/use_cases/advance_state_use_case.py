from modules.order.application.ports.driver.advance_state_ports import (
    AdvanceStateCommand, AdvanceStateResponse, _ALLOWED_TRANSITIONS
)
from modules.order.application.ports.driven.order_repository import OrderRepository
from modules.order.domain.errors.order_errors import OrderNotFound, OrderStateError
from modules.order.domain.models.order_state import OrderState


class AdvanceStateUseCase:
    """
    Advances the order through its post-confirmation lifecycle:
    PENDING -> PAID -> CONFIRMED -> IN_PREPARATION -> READY -> DELIVERED/PICKED_UP
    
    The caller must provide the desired target_state. The use case validates
    that the transition is allowed per the domain rules.
    """

    def __init__(self, order_repo: OrderRepository):
        self.order_repo = order_repo

    def execute(self, command: AdvanceStateCommand) -> AdvanceStateResponse:
        order = self.order_repo.get_by_id(command.order_id)
        if not order:
            raise OrderNotFound(f"Order {command.order_id} not found")

        try:
            target = OrderState(command.target_state)
        except ValueError:
            raise OrderStateError(f"'{command.target_state}' is not a valid order state")

        allowed = _ALLOWED_TRANSITIONS.get(order.status, set())
        if target not in allowed:
            raise OrderStateError(
                f"Cannot transition from {order.status.value} to {target.value}. "
                f"Allowed: {[s.value for s in allowed]}"
            )

        previous = order.status
        order.status = target
        self.order_repo.save(order)

        return AdvanceStateResponse(
            order_id=order.id,
            previous_state=previous.value,
            new_state=order.status.value
        )
