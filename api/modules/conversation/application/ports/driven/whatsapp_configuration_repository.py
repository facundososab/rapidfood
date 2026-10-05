"""Driven port: persist and look up per-business WhatsApp credentials."""
from __future__ import annotations

from typing import Optional, Protocol, runtime_checkable

from modules.conversation.domain.models.whatsapp_configuration import (
    WhatsAppConfiguration,
)


@runtime_checkable
class WhatsAppConfigurationRepositoryPort(Protocol):
    def get_by_business_config_id(
        self, business_config_id: str
    ) -> Optional[WhatsAppConfiguration]: ...

    def get_by_phone_number_id(
        self, phone_number_id: str
    ) -> Optional[WhatsAppConfiguration]: ...

    def list_active(self) -> list[WhatsAppConfiguration]:
        """All active configurations (used to match a webhook verify token)."""
        ...

    def upsert(self, config: WhatsAppConfiguration) -> WhatsAppConfiguration: ...
