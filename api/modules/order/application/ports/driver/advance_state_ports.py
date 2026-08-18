from dataclasses import dataclass
from modules.order.domain.models.order_state import OrderState


# Valid forward state transitions per business rules
_ALLOWED_TRANSITIONS: dict[OrderState, set[OrderState]] = {
    OrderState.PENDING:        {OrderState.PAID},
    OrderState.PAID:           {OrderState.CONFIRMED},
    OrderState.CONFIRMED:      {OrderState.IN_PREPARATION},
    OrderState.IN_PREPARATION: {OrderState.READY},
    OrderState.READY:          {OrderState.DELIVERED, OrderState.PICKED_UP},
}


@dataclass
class AdvanceStateCommand:
    order_id: str
    target_state: str


@dataclass
class AdvanceStateResponse:
    order_id: str
    previous_state: str
    new_state: str
