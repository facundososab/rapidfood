"""Driver port: read the linkage status of one business.

The status is intentionally token-free: the panel only needs to know whether
the business is connected, and to which Mercado Pago account.
"""

from abc import ABC, abstractmethod
from dataclasses import dataclass


@dataclass(frozen=True)
class GetLinkStatusQuery:
    business_config_id: str


@dataclass(frozen=True)
class GetLinkStatusResult:
    linked: bool
    live_mode: bool | None = None
    user_id: str | None = None
    public_key: str | None = None


class GetLinkStatusPort(ABC):
    @abstractmethod
    def execute(self, query: GetLinkStatusQuery) -> GetLinkStatusResult:
        """Return the linkage status of a business, never the tokens."""
        pass
