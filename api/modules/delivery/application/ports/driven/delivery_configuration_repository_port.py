"""DeliveryConfigurationRepositoryPort — driven port.

Abstracts reading and writing the full delivery configuration for a restaurant.
The implementation (Prisma adapter) aggregates data from BusinessConfiguration,
DeliveryPricingConfiguration, DeliveryWeekdayPricingRule, and Address.
"""

from __future__ import annotations

from typing import Optional, Protocol

from modules.delivery.domain.models.delivery_configuration import DeliveryConfiguration


class DeliveryConfigurationRepositoryPort(Protocol):
    """Driven port for persisting and retrieving delivery configuration."""

    def get_by_business_config_id(
        self, business_config_id: str
    ) -> Optional[DeliveryConfiguration]:
        """Return the delivery configuration for the given restaurant, or None."""
        ...

    def save(self, config: DeliveryConfiguration) -> None:
        """Atomically persist the full delivery configuration."""
        ...
