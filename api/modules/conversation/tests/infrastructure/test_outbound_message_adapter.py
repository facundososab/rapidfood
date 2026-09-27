"""Dev outbound adapter: persists the message to the conversation and logs it."""
from __future__ import annotations

import logging
from datetime import datetime, timezone

from modules.conversation.application.ports.driven.outbound_message import (
    OutboundMessage,
)
from modules.conversation.infrastructure.adapters.driven.outbound.dev_outbound_message_adapter import (
    DevOutboundMessageAdapter,
)


class FakeMessageRepo:
    def __init__(self):
        self.added = []

    def add(self, message):
        self.added.append(message)
        return message


class FakeClock:
    def now(self):
        return datetime(2026, 9, 20, tzinfo=timezone.utc)


def test_dev_outbound_persists_the_message_on_the_conversation(caplog):
    repo = FakeMessageRepo()
    adapter = DevOutboundMessageAdapter(repo, FakeClock())

    with caplog.at_level(logging.INFO):
        adapter.send(
            OutboundMessage(
                conversation_id="c-1",
                channel="WHATSAPP",
                destination="+5491112345678",
                content="¡Pago acreditado!",
            )
        )

    assert len(repo.added) == 1
    message = repo.added[0]
    assert message.conversation_id == "c-1"
    assert message.role == "AGENT"
    assert message.content == "¡Pago acreditado!"
    assert message.created_at is not None
    assert "Outbound message" in caplog.text
