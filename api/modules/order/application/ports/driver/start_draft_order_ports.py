from abc import ABC, abstractmethod
from dataclasses import dataclass
from typing import Optional


@dataclass
class StartDraftOrderCommand:
    client_id: Optional[str] = None
    conversation_id: Optional[str] = None
    origin: Optional[str] = None


@dataclass
class StartDraftOrderResponse:
    order_id: str
    status: str


class StartDraftOrderPort(ABC):
    @abstractmethod
    def execute(self, command: StartDraftOrderCommand) -> StartDraftOrderResponse:
        pass
