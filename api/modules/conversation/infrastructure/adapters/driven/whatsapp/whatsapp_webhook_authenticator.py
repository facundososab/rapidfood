"""Infrastructure: authenticate the WhatsApp webhook (token + HMAC signature).

Owns the credentials: it reads the business config, verifies Meta's subscription
token and the ``X-Hub-Signature-256`` HMAC-SHA256, and returns only a SAFE
identity (never the access token / app secret). Keeping this in infrastructure
means the channel driver never touches secrets.
"""
from __future__ import annotations

import hashlib
import hmac
import logging
from typing import Optional

from modules.conversation.application.ports.driven.whatsapp_configuration_repository import (
    WhatsAppConfigurationRepositoryPort,
)
from modules.conversation.application.ports.driver.whatsapp_webhook_ports import (
    WhatsAppWebhookIdentity,
)

logger = logging.getLogger(__name__)


class WhatsAppWebhookAuthenticator:
    def __init__(
        self, repository: WhatsAppConfigurationRepositoryPort
    ) -> None:
        self._repository = repository

    def verify_subscription(self, token: str) -> bool:
        if not token:
            return False
        for config in self._repository.list_active():
            if hmac.compare_digest(config.verify_token, token):
                return True
        return False

    def resolve_identity(
        self, phone_number_id: str
    ) -> Optional[WhatsAppWebhookIdentity]:
        config = self._repository.get_by_phone_number_id(phone_number_id)
        if config is None or not config.is_active:
            return None
        return WhatsAppWebhookIdentity(
            business_config_id=config.business_config_id,
            phone_number_id=config.phone_number_id,
            display_phone_number=config.display_phone_number,
        )

    def verify_signature(
        self, phone_number_id: str, raw_body: bytes, signature_header: str
    ) -> bool:
        config = self._repository.get_by_phone_number_id(phone_number_id)
        if config is None or not config.is_active:
            return False
        return _verify_signature(raw_body, signature_header, config.app_secret)


def _verify_signature(raw_body: bytes, header: str, app_secret: str) -> bool:
    if not header or not app_secret or not header.startswith("sha256="):
        return False
    provided = header.split("=", 1)[1].strip()
    expected = hmac.new(
        app_secret.encode("utf-8"), raw_body, hashlib.sha256
    ).hexdigest()
    return hmac.compare_digest(expected, provided)
