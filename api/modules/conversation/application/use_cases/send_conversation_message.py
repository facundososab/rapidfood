"""Deliver a message to a conversation's own channel (channel-neutral, send-only).

The caller persists the message (if needed); this only dispatches it to the
channel through the outbound port. Which channel and credentials are the
adapter's business — this use case knows nothing about WhatsApp.
"""
from __future__ import annotations

import logging

from modules.conversation.application.ports.driven.outbound_message import (
    OutboundMessage,
    OutboundMessagePort,
)
from modules.conversation.application.ports.driver.whatsapp_messaging_ports import (
    SendConversationMessageCommand,
    SendConversationMessagePort,
)

logger = logging.getLogger(__name__)


class SendConversationMessageUseCase(SendConversationMessagePort):
    def __init__(
        self,
        conversation_repository,
        outbound_message: OutboundMessagePort,
    ) -> None:
        self._conversations = conversation_repository
        self._outbound = outbound_message

    def execute(self, command: SendConversationMessageCommand) -> bool:
        record = self._conversations.get_by_id(command.conversation_id)
        if record is None:
            return False

        destination = getattr(record, "external_thread_id", None)
        if not destination:
            logger.warning(
                "Conversation %s has no external destination; message not sent.",
                command.conversation_id,
            )
            return False

        try:
            self._outbound.send(
                OutboundMessage(
                    conversation_id=command.conversation_id,
                    channel=record.channel,
                    destination=destination,
                    content=command.content,
                )
            )
            return True
        except Exception as exc:
            # Delivery failure (e.g. Meta 131030 on a test number) must not break
            # the panel action; the message is already stored.
            logger.warning("Conversation message delivery failed: %s", exc)
            return False
