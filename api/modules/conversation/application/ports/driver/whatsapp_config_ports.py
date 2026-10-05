"""Driver ports: read/update a business's WhatsApp configuration (panel).

Secrets are write-only: the read view reports only whether a value is set, never
the value itself.
"""
from __future__ import annotations

from dataclasses import dataclass
from typing import Optional, Protocol


@dataclass(frozen=True, slots=True)
class GetWhatsAppConfigurationQuery:
    business_config_id: str


@dataclass(frozen=True, slots=True)
class SaveWhatsAppConfigurationCommand:
    business_config_id: str
    phone_number_id: str
    verify_token: str
    access_token: Optional[str] = None
    app_secret: Optional[str] = None
    api_version: str = "v21.0"
    waba_id: Optional[str] = None
    display_phone_number: Optional[str] = None
    order_paid_template_name: Optional[str] = None
    order_paid_template_lang: Optional[str] = "es_AR"
    is_active: bool = True


@dataclass(frozen=True, slots=True)
class WhatsAppConfigurationView:
    business_config_id: str
    phone_number_id: str
    verify_token: str
    api_version: str
    waba_id: Optional[str] = None
    display_phone_number: Optional[str] = None
    order_paid_template_name: Optional[str] = None
    order_paid_template_lang: Optional[str] = None
    is_active: bool = True
    has_access_token: bool = False
    has_app_secret: bool = False


class GetWhatsAppConfigurationPort(Protocol):
    def execute(
        self, query: GetWhatsAppConfigurationQuery
    ) -> WhatsAppConfigurationView: ...


class SaveWhatsAppConfigurationPort(Protocol):
    def execute(
        self, command: SaveWhatsAppConfigurationCommand
    ) -> WhatsAppConfigurationView: ...
