from dataclasses import dataclass


@dataclass
class CancelOrderCommand:
    order_id: str
    reason: str = ""


@dataclass
class CancelOrderResponse:
    order_id: str
    status: str
