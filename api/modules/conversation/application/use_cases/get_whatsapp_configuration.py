"""Read a business's WhatsApp configuration (secrets masked)."""
from __future__ import annotations

from modules.conversation.application.ports.driven.whatsapp_configuration_repository import (
    WhatsAppConfigurationRepositoryPort,
)
from modules.conversation.application.ports.driver.whatsapp_config_ports import (
    GetWhatsAppConfigurationPort,
    GetWhatsAppConfigurationQuery,
    WhatsAppConfigurationView,
)
from modules.conversation.domain.errors import WhatsAppConfigurationNotFoundError
from modules.conversation.domain.models.whatsapp_configuration import (
    WhatsAppConfiguration,
)


def to_view(config: WhatsAppConfiguration) -> WhatsAppConfigurationView:
    return WhatsAppConfigurationView(
        business_config_id=config.business_config_id,
        phone_number_id=config.phone_number_id,
        verify_token=config.verify_token,
        api_version=config.api_version,
        waba_id=config.waba_id,
        display_phone_number=config.display_phone_number,
        order_paid_template_name=config.order_paid_template_name,
        order_paid_template_lang=config.order_paid_template_lang,
        is_active=config.is_active,
        has_access_token=bool(config.access_token),
        has_app_secret=bool(config.app_secret),
    )


class GetWhatsAppConfigurationUseCase(GetWhatsAppConfigurationPort):
    def __init__(self, repository: WhatsAppConfigurationRepositoryPort) -> None:
        self._repository = repository

    def execute(
        self, query: GetWhatsAppConfigurationQuery
    ) -> WhatsAppConfigurationView:
        config = self._repository.get_by_business_config_id(
            query.business_config_id
        )
        if config is None:
            raise WhatsAppConfigurationNotFoundError(query.business_config_id)
        return to_view(config)
