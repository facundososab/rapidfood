"""Resolve the customer behind a channel identity (WhatsApp phone).

The channel gives us the phone number and the WhatsApp display name; the client
module owns the rule of how a client is found or created from them. This use case
is the conversation module's thin boundary to that rule.
"""
from __future__ import annotations

import logging
from typing import Optional

from modules.conversation.application.ports.driven.client_service import (
    ClientServicePort,
)

logger = logging.getLogger(__name__)


class ResolveClientForChannelUseCase:
    def __init__(self, client_service: Optional[ClientServicePort]) -> None:
        self._client_service = client_service

    def execute(self, display_name: Optional[str], phone: Optional[str]) -> Optional[str]:
        if self._client_service is None or not phone:
            return None
        try:
            return self._client_service.resolve_client(display_name or "", phone)
        except Exception:
            # Never let client resolution break the inbound flow.
            logger.exception("Client resolution failed for phone=%s", phone)
            return None
