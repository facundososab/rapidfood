"""Dev outbound adapter: logs the message and persists it to the conversation.

Stands in for the real channel sender (WhatsApp Cloud API) while it does not
exist: it implements the same ``OutboundMessagePort``, so the customer-facing
message is observable in the panel conversation and in the thread history, and
swapping in the real adapter only touches the composition root.
"""
from __future__ import annotations

import logging
import uuid
from typing import Any

from modules.conversation.application.ports.driven.outbound_message import (
    OutboundMessage,
    OutboundMessagePort,
)
from modules.conversation.domain.models.message import Message
from modules.conversation.domain.value_objects import MessageRole, MessageStatus

logger = logging.getLogger(__name__)


class DevOutboundMessageAdapter(OutboundMessagePort):
    def __init__(self, message_repository: Any, clock: Any) -> None:
        self._messages = message_repository
        self._clock = clock

    def send(self, message: OutboundMessage) -> None:
        logger.info(
            "Outbound message [channel=%s destination=%s conversation=%s]: %s",
            message.channel,
            message.destination,
            message.conversation_id,
            message.content,
        )
        self._messages.add(
            Message(
                message_id=str(uuid.uuid4()),
                conversation_id=message.conversation_id,
                role=MessageRole.AGENT,
                content=message.content,
                status=MessageStatus.PROCESSED,
                created_at=self._clock.now(),
            )
        )
