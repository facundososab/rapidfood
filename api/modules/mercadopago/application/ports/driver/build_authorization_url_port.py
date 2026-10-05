"""Driver port: start the "Connect your Mercado Pago account" flow."""

from abc import ABC, abstractmethod
from dataclasses import dataclass


@dataclass(frozen=True)
class BuildAuthorizationUrlCommand:
    business_config_id: str


@dataclass(frozen=True)
class BuildAuthorizationUrlResult:
    authorization_url: str


class BuildAuthorizationUrlPort(ABC):
    @abstractmethod
    def execute(
        self,
        command: BuildAuthorizationUrlCommand,
    ) -> BuildAuthorizationUrlResult:
        """Return the Mercado Pago authorization URL for one business."""
        pass
