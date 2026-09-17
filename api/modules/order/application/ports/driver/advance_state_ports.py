from dataclasses import dataclass


@dataclass
class AdvanceStateCommand:
    order_id: str
    target_state: str


@dataclass
class AdvanceStateResponse:
    order_id: str
    previous_state: str
    new_state: str
