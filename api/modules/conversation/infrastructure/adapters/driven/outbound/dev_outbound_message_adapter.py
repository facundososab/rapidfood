"""Dev outbound adapter: logs the message (send-only).

Stands in for the real channel sender (WhatsApp Cloud API) when it is not wired.
It implements the same ``OutboundMessagePort``; persistence is the caller's job,
so switching to the real adapter only touches the composition root.
"""
from __future__ import annotations

import logging

from modules.conversation.application.ports.driven.outbound_message import (
    OutboundMessage,
    OutboundMessagePort,
)

logger = logging.getLogger(__name__)


class DevOutboundMessageAdapter(OutboundMessagePort):
    def __init__(self) -> None:
        pass

    def send(self, message: OutboundMessage) -> None:
        logger.info(
            "Outbound message [channel=%s destination=%s conversation=%s]: %s",
            message.channel,
            message.destination,
            message.conversation_id,
            message.content,
        )
