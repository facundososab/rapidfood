"""Complete a partially given delivery address with the restaurant's own data.

The customer usually says "San Juan 3250"; the city and province are the
restaurant's. This keeps the agent from interrogating the customer for data it
can resolve itself, while still refusing to guess when there is nothing to fall
back on.
"""
from __future__ import annotations

import dataclasses
from typing import Optional

from modules.conversation.application.ports.driven.business_service import (
    BusinessAddressDTO,
)
from modules.conversation.application.ports.driver.agent_commands import AddressCommand
from modules.conversation.domain.errors import AgentBusinessError


def complete_address(
    address: AddressCommand, defaults: Optional[BusinessAddressDTO]
) -> AddressCommand:
    if defaults is None:
        return address
    return dataclasses.replace(
        address,
        city=(address.city or "").strip() or defaults.city,
        province=(address.province or "").strip() or defaults.province,
        postal_code=(address.postal_code or "").strip() or defaults.postal_code,
    )


def require_deliverable_address(address: AddressCommand) -> AddressCommand:
    """A delivery quote needs at least street, number, city and province."""
    missing = [
        label
        for label, value in (
            ("calle", address.street),
            ("número", address.street_number),
            ("ciudad", address.city),
            ("provincia", address.province),
        )
        if not (value or "").strip()
    ]
    if missing:
        raise AgentBusinessError(
            "Me falta " + ", ".join(missing) + " para calcular el envío.",
            code="DELIVERY_ADDRESS_REQUIRED",
        )
    return address
