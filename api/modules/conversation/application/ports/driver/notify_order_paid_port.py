from abc import ABC, abstractmethod
from dataclasses import dataclass


@dataclass
class NotifyOrderPaidCommand:
    conversation_id: str
    order_id: str


class NotifyOrderPaidPort(ABC):
    @abstractmethod
    def execute(self, command: NotifyOrderPaidCommand) -> bool:
        """Send the "order paid" confirmation to the customer's channel.

        Returns True when a message was produced, False when the conversation is
        unknown (nothing to notify).
        """
        pass
