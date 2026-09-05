"""BusinessConfigurationRepositoryPort — driven port."""

from __future__ import annotations

from typing import Optional, Protocol

from modules.business.domain.models.business_configuration import (
    Address,
    BusinessConfiguration,
    BusinessHours,
)


class BusinessConfigurationRepositoryPort(Protocol):
    def get_by_id(self, business_config_id: str) -> Optional[BusinessConfiguration]:
        """Return BusinessConfiguration with all businessHours and addresses, or None."""
        ...

    def save_general(
        self,
        business_config_id: str,
        *,
        business_name: str,
        min_order: object,
        shipping_cost: object,
    ) -> BusinessConfiguration:
        """Upsert the basic fields. Raises BusinessConfigurationNotFoundError if not found."""
        ...

    def replace_business_hours(
        self,
        business_config_id: str,
        hours: list[BusinessHours],
    ) -> None:
        """Delete all existing hours for this business and insert the provided list."""
        ...

    def create_address(
        self,
        business_config_id: str,
        *,
        street: str,
        street_number: str,
        city: str,
        province: str,
        floor: Optional[str],
        apartment: Optional[str],
        postal_code: Optional[str],
    ) -> Address:
        """Create a new address for this business."""
        ...

    def update_address(
        self,
        address_id: str,
        *,
        street: str,
        street_number: str,
        city: str,
        province: str,
        floor: Optional[str],
        apartment: Optional[str],
        postal_code: Optional[str],
    ) -> Address:
        """Update an existing address."""
        ...

    def delete_address(self, address_id: str) -> None:
        """Delete an address by id."""
        ...

    def get_address_by_id(self, address_id: str) -> Optional[Address]:
        """Return an Address by id, or None."""
        ...
