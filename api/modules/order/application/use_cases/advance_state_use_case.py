from modules.order.application.ports.driver.advance_state_ports import (
    AdvanceStateCommand, AdvanceStateResponse
)
from modules.order.application.ports.driven.order_repository import OrderRepository
from modules.order.domain.errors.order_errors import OrderNotFound, OrderStateError
from modules.order.domain.models.order_state import OrderState
from modules.order.domain.services.state_transitions import (
    allowed_transitions,
    can_transition,
)


class AdvanceStateUseCase:
    """
    Advances the order through its post-confirmation lifecycle. The allowed
    transitions are centralized in the domain (state_transitions) so this use
    case cannot drift from the rest of the machine.
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

        if not can_transition(order.status, target, order.payment_type):
            allowed = allowed_transitions(order.status, order.payment_type)
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
