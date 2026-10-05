"""Driver port: unlink the Mercado Pago account of one business."""

from abc import ABC, abstractmethod
from dataclasses import dataclass


@dataclass(frozen=True)
class UnlinkMercadoPagoAccountCommand:
    business_config_id: str


class UnlinkMercadoPagoAccountPort(ABC):
    @abstractmethod
    def execute(self, command: UnlinkMercadoPagoAccountCommand) -> None:
        """Remove the link. Idempotent: unlinking an unlinked business succeeds."""
        pass
