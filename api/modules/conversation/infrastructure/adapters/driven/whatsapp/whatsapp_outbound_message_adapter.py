"""Real outbound adapter: delivers a message to WhatsApp (SEND-ONLY).

Replaces ``DevOutboundMessageAdapter`` in production wiring. It resolves the
business's credentials and decides between free-form text and an approved
template using the 24h customer service window.

It does NOT persist: callers persist the message themselves, so reply paths
(whose message is already stored) never duplicate it in the panel thread.

Delivery mode rule (Meta policy):
- window open (customer messaged within 24h) -> free-form ``text``;
- window closed -> a template is REQUIRED. When the business has configured
  ``orderPaidTemplateName`` it is sent; otherwise the free-form attempt is left
  to fail loudly (Meta rejects it), which is the honest outcome.

Non-WhatsApp channels are ignored here (no adapter for them).
"""
from __future__ import annotations

import logging
from typing import Any

from modules.conversation.application.ports.driven.outbound_message import (
    OutboundMessage,
    OutboundMessagePort,
)
from modules.conversation.domain.services.customer_service_window import (
    is_customer_service_window_open,
)

logger = logging.getLogger(__name__)

CHANNEL = "WHATSAPP"


class WhatsAppOutboundMessageAdapter(OutboundMessagePort):
    def __init__(
        self,
        sender: Any,
        config_repository: Any,
        conversation_repository: Any,
        message_repository: Any,
        clock: Any,
    ) -> None:
        self._sender = sender
        self._configs = config_repository
        self._conversations = conversation_repository
        self._messages = message_repository
        self._clock = clock

    def send(self, message: OutboundMessage) -> None:
        if str(message.channel) != CHANNEL:
            logger.info(
                "No outbound adapter for channel=%s; message not delivered.",
                message.channel,
            )
            return

        record = self._conversations.get_by_id(message.conversation_id)
        destination = message.destination or (
            getattr(record, "external_thread_id", None) if record else None
        )
        if record is None or not destination:
            logger.warning(
                "Outbound WhatsApp message has no destination (conversation=%s)",
                message.conversation_id,
            )
            return

        config = self._configs.get_by_business_config_id(record.business_config_id)
        if config is None or not getattr(config, "is_active", False):
            logger.warning(
                "No active WhatsApp configuration for business %s; message not sent.",
                getattr(record, "business_config_id", None),
            )
            return

        window_open = is_customer_service_window_open(
            self._messages.list_by_conversation(message.conversation_id),
            self._clock.now(),
        )
        if window_open or not getattr(config, "has_order_paid_template", False):
            self._sender.send_text(config=config, to=destination, body=message.content)
            return

        self._sender.send_template(
            config=config,
            to=destination,
            template_name=config.order_paid_template_name,
            language_code=config.order_paid_template_lang or "es_AR",
            body_params=(message.content,),
        )
