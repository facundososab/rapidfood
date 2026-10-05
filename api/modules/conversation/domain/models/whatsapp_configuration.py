"""WhatsApp Cloud API credentials for one business (per-business integration).

The channel is owned by the conversation module, so its credentials live here.
Secrets are held in plaintext ONLY in memory; the repository encrypts them at
persistence time and the REST layer never returns them.
"""
from __future__ import annotations

from dataclasses import dataclass
from typing import Optional

from modules.conversation.domain.errors import WhatsAppConfigurationValidationError

# WhatsApp Graph API version used when the caller does not pin one.
DEFAULT_API_VERSION = "v21.0"


@dataclass(slots=True)
class WhatsAppConfiguration:
    business_config_id: str
    phone_number_id: str
    verify_token: str
    access_token: str
    app_secret: str
    api_version: str = DEFAULT_API_VERSION
    waba_id: Optional[str] = None
    display_phone_number: Optional[str] = None
    order_paid_template_name: Optional[str] = None
    order_paid_template_lang: Optional[str] = "es_AR"
    is_active: bool = True
    id: Optional[str] = None

    def __post_init__(self) -> None:
        if not self.business_config_id:
            raise WhatsAppConfigurationValidationError(
                "business_config_id is required"
            )
        if not self.phone_number_id:
            raise WhatsAppConfigurationValidationError("phone_number_id is required")
        if not self.verify_token:
            raise WhatsAppConfigurationValidationError("verify_token is required")
        # Secrets are intentionally NOT required here: a stored configuration can
        # exist while its secrets are unreadable (e.g. the encryption key was
        # rotated), and the read path must still describe it so the operator can
        # re-enter them. The save use case enforces that secrets are present.
        self.api_version = (self.api_version or DEFAULT_API_VERSION).strip()

    @property
    def has_order_paid_template(self) -> bool:
        return bool(self.order_paid_template_name)
