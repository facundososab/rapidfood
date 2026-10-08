"""Public contact profile for the digital menu (never exposes secrets)."""
from __future__ import annotations

from modules.conversation.application.ports.driver.public_contact_ports import (
    GetPublicContactPort,
    PublicContactView,
)


class GetPublicContactUseCase(GetPublicContactPort):
    def __init__(self, whatsapp_config_repository, business_service=None) -> None:
        self._whatsapp_config_repository = whatsapp_config_repository
        self._business_service = business_service

    def execute(self, business_configuration_id: str) -> PublicContactView:
        name = None
        if self._business_service is not None:
            try:
                name = self._business_service.get_name(business_configuration_id)
            except Exception:
                name = None

        config = None
        try:
            config = self._whatsapp_config_repository.get_by_business_config_id(
                business_configuration_id
            )
        except Exception:
            config = None

        number = (config.display_phone_number or None) if config else None
        enabled = bool(config.is_active) if config else False

        return PublicContactView(
            business_name=name,
            whatsapp_number=number,
            whatsapp_enabled=enabled,
        )
