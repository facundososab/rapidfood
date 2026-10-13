"""Public contact profile for the digital menu (never exposes secrets).

This read is intentionally thin: it delegates to its ports and lets real failures
surface. Degrading the public HTTP response is the REST driver's concern, not an
application rule, so no broad ``except`` lives here.
"""
from __future__ import annotations

from modules.conversation.application.ports.driver.public_contact_ports import (
    GetPublicContactPort,
    PublicContact,
)


class GetPublicContactUseCase(GetPublicContactPort):
    def __init__(self, whatsapp_config_repository, business_service=None) -> None:
        self._whatsapp_config_repository = whatsapp_config_repository
        self._business_service = business_service

    def execute(self, business_configuration_id: str) -> PublicContact:
        name = (
            self._business_service.get_name(business_configuration_id)
            if self._business_service is not None
            else None
        )

        config = self._whatsapp_config_repository.get_by_business_config_id(
            business_configuration_id
        )

        return PublicContact(
            business_name=name,
            whatsapp_number=(config.display_phone_number or None) if config else None,
            whatsapp_enabled=bool(config.is_active) if config else False,
        )
