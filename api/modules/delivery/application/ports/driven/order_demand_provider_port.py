"""OrderDemandProviderPort — driven port.

Counts currently active delivery orders for a specific restaurant.
'Active' means the order is in a state that still represents real kitchen/delivery load:
CONFIRMED or IN_PREPARATION.
"""

from __future__ import annotations

from typing import Protocol


class OrderDemandProviderPort(Protocol):
    """Driven port for counting active delivery orders per restaurant."""

    def count_active_delivery_orders(
        self,
        business_config_id: str,
    ) -> int:
        """Return the number of currently active delivery orders.

        Only counts orders with:
            - businessConfigId == business_config_id
            - deliveryType == DELIVERY
            - status in {CONFIRMED, IN_PREPARATION}

        Args:
            business_config_id: The restaurant's configuration identifier.

        Returns:
            Count of qualifying orders.
        """
        ...
