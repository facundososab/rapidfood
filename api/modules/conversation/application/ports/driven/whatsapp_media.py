"""Driven port: download inbound media from the WhatsApp Cloud API.

Media messages (audio, image, ...) arrive as a media id; the bytes are fetched
in two steps (resolve the id to a temporary URL, then download it). Implemented
by the same Graph client that sends messages.
"""
from __future__ import annotations

from typing import Optional, Protocol, Tuple, runtime_checkable

from modules.conversation.domain.models.whatsapp_configuration import (
    WhatsAppConfiguration,
)


@runtime_checkable
class WhatsAppMediaPort(Protocol):
    def download_media(
        self, *, config: WhatsAppConfiguration, media_id: str
    ) -> Tuple[bytes, Optional[str]]:
        """Return (bytes, mime_type) for the media, or raise on failure."""
        ...
