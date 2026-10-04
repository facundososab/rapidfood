"""Driven port: send messages through the WhatsApp Cloud API.

The application resolves the credentials; this port only knows how to speak to
the channel. Implemented by the requests-based ``WhatsAppCloudClient``.
"""
from __future__ import annotations

from typing import Protocol, Sequence, runtime_checkable

from modules.conversation.domain.models.whatsapp_configuration import (
    WhatsAppConfiguration,
)


@runtime_checkable
class WhatsAppSenderPort(Protocol):
    def send_text(
        self, *, config: WhatsAppConfiguration, to: str, body: str
    ) -> None: ...

    def send_template(
        self,
        *,
        config: WhatsAppConfiguration,
        to: str,
        template_name: str,
        language_code: str,
        body_params: Sequence[str] = (),
    ) -> None: ...
