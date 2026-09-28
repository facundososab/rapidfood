from abc import ABC, abstractmethod
from dataclasses import dataclass
from typing import Optional


@dataclass
class GetOrCreateCurrentDraftCommand:
    business_config_id: str
    conversation_id: str
    client_id: Optional[str] = None
    client_name: Optional[str] = None
    origin: Optional[str] = None


@dataclass
class GetOrCreateCurrentDraftResult:
    order_id: str
    status: str
    created: bool


class GetOrCreateCurrentDraftPort(ABC):
    @abstractmethod
    def execute(
        self, command: GetOrCreateCurrentDraftCommand
    ) -> GetOrCreateCurrentDraftResult:
        pass
