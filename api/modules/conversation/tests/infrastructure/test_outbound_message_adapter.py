"""Dev outbound adapter: logs the message (send-only, no persistence)."""
from __future__ import annotations

import logging

from modules.conversation.application.ports.driven.outbound_message import (
    OutboundMessage,
)
from modules.conversation.infrastructure.adapters.driven.outbound.dev_outbound_message_adapter import (
    DevOutboundMessageAdapter,
)


def test_dev_outbound_logs_the_message(caplog):
    adapter = DevOutboundMessageAdapter()

    with caplog.at_level(logging.INFO):
        adapter.send(
            OutboundMessage(
                conversation_id="c-1",
                channel="WHATSAPP",
                destination="+5491112345678",
                content="¡Pago acreditado!",
            )
        )

    assert "Outbound message" in caplog.text
    assert "¡Pago acreditado!" in caplog.text
