"""Driver port: close a conversation's current order and open a fresh draft.

Used when a channel decides a conversation has gone idle (a new session started)
and the previous, never-completed order must not absorb the new one. The order
module owns the state change; the caller only decides WHEN.
"""
from __future__ import annotations

from abc import ABC, abstractmethod
from dataclasses import dataclass
from typing import Optional


@dataclass(frozen=True)
class RestartConversationOrderCommand:
    business_config_id: str
    conversation_id: str
    # Optional customer to carry over to the fresh draft.
    client_id: Optional[str] = None
    client_name: Optional[str] = None


@dataclass(frozen=True)
class RestartConversationOrderResponse:
    # The order that was closed (None when there was nothing to restart).
    previous_order_id: Optional[str]
    # The freshly opened draft (None when there was nothing to restart).
    order_id: Optional[str]
    created: bool


class RestartConversationOrderPort(ABC):
    @abstractmethod
    def execute(
        self, command: RestartConversationOrderCommand
    ) -> RestartConversationOrderResponse:
        ...
