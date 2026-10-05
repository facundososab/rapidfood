"""Prisma-backed repository for per-business WhatsApp credentials.

Secrets are encrypted with `CredentialCipher` on write and decrypted on read, so
plaintext never reaches the database.
"""
from __future__ import annotations

import logging
import uuid
from typing import Optional

from modules.conversation.application.ports.driven.whatsapp_configuration_repository import (
    WhatsAppConfigurationRepositoryPort,
)
from modules.conversation.domain.models.whatsapp_configuration import (
    WhatsAppConfiguration,
)
from modules.conversation.infrastructure.adapters.driven.whatsapp.credential_cipher import (
    CredentialCipher,
)

logger = logging.getLogger(__name__)


class PrismaWhatsAppConfigurationRepository(WhatsAppConfigurationRepositoryPort):
    def __init__(self, client=None, cipher: Optional[CredentialCipher] = None) -> None:
        self._client = client
        self._cipher = cipher or CredentialCipher()

    @property
    def _db(self):
        if self._client is not None:
            return self._client
        from shared.infrastructure.prisma.db import db

        return db.client

    def get_by_business_config_id(
        self, business_config_id: str
    ) -> Optional[WhatsAppConfiguration]:
        row = self._db.whatsappconfiguration.find_unique(
            where={"businessConfigId": business_config_id}
        )
        return self._to_domain(row) if row else None

    def get_by_phone_number_id(
        self, phone_number_id: str
    ) -> Optional[WhatsAppConfiguration]:
        row = self._db.whatsappconfiguration.find_unique(
            where={"phoneNumberId": phone_number_id}
        )
        return self._to_domain(row) if row else None

    def list_active(self) -> list[WhatsAppConfiguration]:
        rows = self._db.whatsappconfiguration.find_many(where={"isActive": True})
        return [self._to_domain(row) for row in rows]

    def upsert(self, config: WhatsAppConfiguration) -> WhatsAppConfiguration:
        data = {
            "businessConfigId": config.business_config_id,
            "phoneNumberId": config.phone_number_id,
            "wabaId": config.waba_id,
            "displayPhoneNumber": config.display_phone_number,
            "verifyToken": config.verify_token,
            "accessTokenEnc": self._cipher.encrypt(config.access_token),
            "appSecretEnc": self._cipher.encrypt(config.app_secret),
            "apiVersion": config.api_version,
            "orderPaidTemplateName": config.order_paid_template_name,
            "orderPaidTemplateLang": config.order_paid_template_lang,
            "isActive": config.is_active,
        }
        row = self._db.whatsappconfiguration.upsert(
            where={"businessConfigId": config.business_config_id},
            data={
                "create": {**data, "id": config.id or str(uuid.uuid4())},
                "update": data,
            },
        )
        return self._to_domain(row)

    def _to_domain(self, row) -> WhatsAppConfiguration:
        return WhatsAppConfiguration(
            id=row.id,
            business_config_id=row.businessConfigId,
            phone_number_id=row.phoneNumberId,
            verify_token=row.verifyToken,
            access_token=self._safe_decrypt(row.accessTokenEnc),
            app_secret=self._safe_decrypt(row.appSecretEnc),
            api_version=row.apiVersion,
            waba_id=row.wabaId,
            display_phone_number=row.displayPhoneNumber,
            order_paid_template_name=row.orderPaidTemplateName,
            order_paid_template_lang=row.orderPaidTemplateLang,
            is_active=bool(row.isActive),
        )

    def _safe_decrypt(self, value: Optional[str]) -> str:
        """Decrypt a stored secret, degrading to '' when the key no longer matches.

        A rotated/added encryption key makes old ciphertext unreadable. Crashing
        here would take the whole configuration panel down; returning '' lets the
        panel show the config with the secret marked as not loaded, so the
        operator can re-enter it. The failure is logged, never silent.
        """
        if not value:
            return ""
        try:
            return self._cipher.decrypt(value) or ""
        except Exception:
            logger.warning(
                "Stored WhatsApp secret could not be decrypted (encryption key "
                "changed?). The configuration loads with the secret unset."
            )
            return ""
