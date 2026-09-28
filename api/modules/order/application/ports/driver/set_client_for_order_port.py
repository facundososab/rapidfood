from abc import ABC, abstractmethod
from dataclasses import dataclass
from typing import Optional


@dataclass
class SetClientForOrderCommand:
    """Attach the customer's identity to a draft order.

    ``client_id`` links a registered client; ``client_name`` is the always-kept
    snapshot so an order stays attributable even without a client record.
    """

    order_id: str
    client_name: Optional[str] = None
    client_id: Optional[str] = None


@dataclass
class SetClientForOrderResponse:
    order_id: str
    client_id: Optional[str]
    client_name: Optional[str]


class SetClientForOrderPort(ABC):
    @abstractmethod
    def execute(self, command: SetClientForOrderCommand) -> SetClientForOrderResponse:
        pass
