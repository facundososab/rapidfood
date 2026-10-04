"""Infrastructure: turn an inbound WhatsApp voice note into text.

This is a channel-adapter capability, not an application use case: it resolves
the business credentials, downloads the media from the Graph API, and calls the
STT provider (a channel-agnostic port). It returns None when the audio cannot be
transcribed so the driver can reply with a friendly fallback.
"""
from __future__ import annotations

import logging
from typing import Optional

from modules.conversation.application.ports.driven.transcription import (
    TranscriptionPort,
)
from modules.conversation.application.ports.driven.whatsapp_configuration_repository import (
    WhatsAppConfigurationRepositoryPort,
)
from modules.conversation.application.ports.driven.whatsapp_media import (
    WhatsAppMediaPort,
)

logger = logging.getLogger(__name__)


class WhatsAppInboundAudioTranscriber:
    def __init__(
        self,
        repository: WhatsAppConfigurationRepositoryPort,
        media: WhatsAppMediaPort,
        transcriber: TranscriptionPort,
        language: Optional[str] = None,
    ) -> None:
        self._repository = repository
        self._media = media
        self._transcriber = transcriber
        self._language = language

    def transcribe(
        self,
        phone_number_id: str,
        media_id: str,
        mime_type: Optional[str] = None,
    ) -> Optional[str]:
        config = self._repository.get_by_phone_number_id(phone_number_id)
        if config is None or not config.is_active:
            logger.warning(
                "No active WhatsApp config for %s; audio not transcribed.",
                phone_number_id,
            )
            return None

        try:
            audio, downloaded_mime = self._media.download_media(
                config=config, media_id=media_id
            )
        except Exception:
            logger.exception("Inbound WhatsApp media download failed")
            return None

        try:
            text = self._transcriber.transcribe(
                audio=audio,
                mime_type=downloaded_mime or mime_type,
                language=self._language,
            )
        except Exception:
            logger.exception("Inbound WhatsApp audio transcription failed")
            return None

        text = (text or "").strip()
        return text or None
