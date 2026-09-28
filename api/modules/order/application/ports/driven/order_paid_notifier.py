"""Driven port: let the order module announce a paid order to the customer.

The order module must not know how a channel works (that is the conversation
module's job), so it depends on this small port. The composition root implements
it by delegating to the conversation module's notification use case. Calls are
POST-COMMIT and best effort: a notification failure never affects the order.
"""
from typing import Protocol, runtime_checkable


@runtime_checkable
class OrderPaidNotifierPort(Protocol):
    def notify_order_paid(self, *, conversation_id: str, order_id: str) -> None: ...
