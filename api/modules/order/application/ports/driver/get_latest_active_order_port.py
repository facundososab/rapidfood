from abc import ABC, abstractmethod
from dataclasses import dataclass
from typing import Optional

from modules.order.domain.models.order import Order


@dataclass
class GetLatestActiveOrderQuery:
    business_config_id: str
    client_id: Optional[str] = None
    conversation_id: Optional[str] = None


class GetLatestActiveOrderPort(ABC):
    @abstractmethod
    def execute(self, query: GetLatestActiveOrderQuery) -> Optional[Order]:
        pass
