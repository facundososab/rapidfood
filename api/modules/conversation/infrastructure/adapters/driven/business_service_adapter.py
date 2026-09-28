"""Adapts the business module's public query port to `BusinessServicePort`."""
from __future__ import annotations

from typing import Any, Optional

from modules.business.application.ports.driver.get_business_configuration_port import (
    GetBusinessConfigurationQuery,
)
from modules.conversation.application.ports.driven.business_service import (
    BusinessAddressDTO,
    BusinessServicePort,
)


class BusinessServiceAdapter(BusinessServicePort):
    def __init__(self, get_configuration: Any) -> None:
        self._get_configuration = get_configuration

    def get_address(
        self, business_configuration_id: str
    ) -> Optional[BusinessAddressDTO]:
        try:
            config = self._get_configuration.execute(
                GetBusinessConfigurationQuery(
                    business_config_id=business_configuration_id
                )
            )
        except Exception:
            # The restaurant address is a convenience; never fail a turn for it.
            return None

        addresses = config.get("addresses") or []
        if not addresses:
            return None
        address = addresses[0]
        return BusinessAddressDTO(
            city=address.get("city"),
            province=address.get("province"),
            postal_code=address.get("postalCode"),
        )
