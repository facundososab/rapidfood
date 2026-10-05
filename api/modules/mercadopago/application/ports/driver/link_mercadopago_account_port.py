"""Driver port: complete the OAuth callback and link the account."""

from abc import ABC, abstractmethod
from dataclasses import dataclass


@dataclass(frozen=True)
class LinkMercadoPagoAccountCommand:
    code: str
    state: str
    # Optional override: Mercado Pago redirects the browser with no redirect_uri,
    # so the configured one is used when this is omitted.
    redirect_uri: str | None = None


@dataclass(frozen=True)
class LinkMercadoPagoAccountResult:
    credential_id: str | None
    business_config_id: str
    live_mode: bool
    user_id: str | None = None


class LinkMercadoPagoAccountPort(ABC):
    @abstractmethod
    def execute(
        self,
        command: LinkMercadoPagoAccountCommand,
    ) -> LinkMercadoPagoAccountResult:
        """Validate the OAuth state, exchange the code and persist the tokens."""
        pass
