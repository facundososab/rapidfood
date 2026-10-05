"""Driver port: read the plain Mercado Pago access token linked by a business.

Module-internal by design: the token is a credential, so it is never exposed by
the REST driver. Sibling contexts that must charge or reconcile on behalf of a
business (the order checkout and webhook flows) consume this port through an
app-level adapter.
"""

from abc import ABC, abstractmethod
from dataclasses import dataclass


@dataclass(frozen=True)
class GetMercadoPagoAccessTokenQuery:
    business_config_id: str


class GetMercadoPagoAccessTokenPort(ABC):
    @abstractmethod
    def execute(self, query: GetMercadoPagoAccessTokenQuery) -> str | None:
        """Return the linked plain access token, or ``None`` when unlinked."""
        pass
