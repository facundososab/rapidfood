"""OrderDemandProviderPort — driven port.

Counts recent active delivery orders for a specific restaurant within a
given time window. The use case uses this count to determine demand level;
the classification itself is pure domain logic.
"""

from __future__ import annotations

from datetime import datetime
from typing import Protocol


class OrderDemandProviderPort(Protocol):
    """Driven port for counting active delivery orders per restaurant."""

    def count_recent_active_delivery_orders(
        self,
        business_config_id: str,
        since: datetime,
    ) -> int:
        """Return the number of active delivery orders since the given datetime.

        Only counts orders with:
            - businessConfigId == business_config_id
            - deliveryType == DELIVERY
            - createdAt >= since
            - status in {PENDING, PAID, CONFIRMED, IN_PREPARATION, READY}

        Args:
            business_config_id: The restaurant's configuration identifier.
            since: Inclusive lower bound for createdAt filter.

        Returns:
            Count of qualifying orders.
        """
        ...
