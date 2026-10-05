"""Create or update a business's WhatsApp configuration.

Secrets (access token, app secret) are optional on update: when omitted the
stored value is kept, so the panel can edit non-secret fields without forcing the
operator to paste the secret again. A first-time save requires both.
"""
from __future__ import annotations

from modules.conversation.application.ports.driven.whatsapp_configuration_repository import (
    WhatsAppConfigurationRepositoryPort,
)
from modules.conversation.application.ports.driver.whatsapp_config_ports import (
    SaveWhatsAppConfigurationCommand,
    SaveWhatsAppConfigurationPort,
    WhatsAppConfigurationView,
)
from modules.conversation.application.use_cases.get_whatsapp_configuration import (
    to_view,
)
from modules.conversation.domain.errors import WhatsAppConfigurationValidationError
from modules.conversation.domain.models.whatsapp_configuration import (
    WhatsAppConfiguration,
)


class SaveWhatsAppConfigurationUseCase(SaveWhatsAppConfigurationPort):
    def __init__(self, repository: WhatsAppConfigurationRepositoryPort) -> None:
        self._repository = repository

    def execute(
        self, command: SaveWhatsAppConfigurationCommand
    ) -> WhatsAppConfigurationView:
        existing = self._repository.get_by_business_config_id(
            command.business_config_id
        )

        access_token = _clean(command.access_token) or (
            existing.access_token if existing else None
        )
        app_secret = _clean(command.app_secret) or (
            existing.app_secret if existing else None
        )
        if not access_token:
            raise WhatsAppConfigurationValidationError("access_token is required")
        if not app_secret:
            raise WhatsAppConfigurationValidationError("app_secret is required")

        config = WhatsAppConfiguration(
            business_config_id=command.business_config_id,
            phone_number_id=command.phone_number_id.strip(),
            verify_token=command.verify_token.strip(),
            access_token=access_token,
            app_secret=app_secret,
            api_version=command.api_version or "v21.0",
            waba_id=_clean(command.waba_id),
            display_phone_number=_clean(command.display_phone_number),
            order_paid_template_name=_clean(command.order_paid_template_name),
            order_paid_template_lang=(
                _clean(command.order_paid_template_lang) or "es_AR"
            ),
            is_active=bool(command.is_active),
            id=existing.id if existing else None,
        )
        saved = self._repository.upsert(config)
        return to_view(saved)


def _clean(value):
    if value is None:
        return None
    value = value.strip()
    return value or None
