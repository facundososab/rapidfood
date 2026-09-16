"""DeliveryConfiguration aggregate.

Represents the complete delivery setup for a single restaurant.
It is assembled by the repository from multiple Prisma tables but is
not itself a table — it's a domain-level composition.
"""

from __future__ import annotations

from dataclasses import dataclass
from decimal import Decimal
from typing import Optional

from modules.delivery.domain.models.coordinates import Coordinates
from modules.delivery.domain.models.delivery_pricing_config import DeliveryPricingConfig
from modules.delivery.domain.models.delivery_zone import DeliveryZone
from modules.delivery.domain.models.postal_address import PostalAddress


@dataclass
class DeliveryConfiguration:
    """Full delivery configuration for a restaurant."""

    business_config_id: str
    # base cost taken from BusinessConfiguration.shippingCost
    base_shipping_cost: Decimal
    # The address ID chosen as the delivery origin
    origin_address_id: str
    # Resolved address for geocoding; None means not yet geocoded in this session
    origin_address: PostalAddress
    # None means the zone hasn't been configured yet
    delivery_zone: Optional[DeliveryZone]
    pricing_config: Optional[DeliveryPricingConfig]

    @property
    def is_fully_configured(self) -> bool:
        """True only when zone AND pricing are both set."""
        return self.delivery_zone is not None and self.pricing_config is not None
