from datetime import datetime, timedelta, timezone

from modules.conversation.application.ports.driven.outbound_message import (
    OutboundMessage,
)
from modules.conversation.domain.models.conversation import Conversation
from modules.conversation.domain.models.message import Message
from modules.conversation.domain.models.whatsapp_configuration import (
    WhatsAppConfiguration,
)
from modules.conversation.domain.value_objects import MessageRole
from modules.conversation.infrastructure.adapters.driven.whatsapp.whatsapp_outbound_message_adapter import (
    WhatsAppOutboundMessageAdapter,
)
from modules.conversation.tests.fakes import (
    FakeWhatsAppSender,
    InMemoryConversationRepository,
    InMemoryMessageRepository,
    InMemoryWhatsAppConfigurationRepository,
)

NOW = datetime(2026, 10, 2, 12, 0, tzinfo=timezone.utc)


class FakeClock:
    def now(self):
        return NOW


def _conversation():
    return Conversation(
        conversation_id="c1",
        channel="WHATSAPP",
        external_thread_id="5491100000000",
        business_config_id="biz-1",
    )


def _message(role, created_at):
    return Message(
        message_id=f"m-{role}-{created_at.timestamp()}",
        conversation_id="c1",
        role=role,
        content="hola",
        created_at=created_at,
    )


def _adapter(*, template_name=None, user_message_at=None):
    conversations = InMemoryConversationRepository()
    conversations.create(_conversation())
    messages = InMemoryMessageRepository()
    if user_message_at is not None:
        messages.add(_message(MessageRole.USER, user_message_at))
    configs = InMemoryWhatsAppConfigurationRepository()
    configs.upsert(
        WhatsAppConfiguration(
            business_config_id="biz-1",
            phone_number_id="123456",
            verify_token="vt",
            access_token="t",
            app_secret="s",
            order_paid_template_name=template_name,
        )
    )
    sender = FakeWhatsAppSender()
    adapter = WhatsAppOutboundMessageAdapter(
        sender, configs, conversations, messages, FakeClock()
    )
    return adapter, sender, messages


def _outbound():
    return OutboundMessage(
        conversation_id="c1",
        channel="WHATSAPP",
        destination="5491100000000",
        content="Tu pedido fue confirmado",
    )


def test_window_open_sends_free_form_even_with_template():
    adapter, sender, _ = _adapter(
        template_name="order_paid", user_message_at=NOW - timedelta(hours=1)
    )
    adapter.send(_outbound())
    assert sender.texts == [("123456", "5491100000000", "Tu pedido fue confirmado")]
    assert sender.templates == []


def test_window_closed_uses_template_when_configured():
    adapter, sender, _ = _adapter(
        template_name="order_paid", user_message_at=NOW - timedelta(hours=30)
    )
    adapter.send(_outbound())
    assert sender.texts == []
    assert sender.templates == [
        ("123456", "5491100000000", "order_paid", "es_AR", ("Tu pedido fue confirmado",))
    ]


def test_window_closed_without_template_falls_back_to_text():
    adapter, sender, _ = _adapter(
        template_name=None, user_message_at=NOW - timedelta(hours=30)
    )
    adapter.send(_outbound())
    assert len(sender.texts) == 1
    assert sender.templates == []


def test_the_adapter_does_not_persist():
    adapter, _, messages = _adapter(user_message_at=NOW - timedelta(hours=1))
    adapter.send(_outbound())
    # Send-only: the caller owns persistence, so nothing new is stored here.
    assert not any(
        m.content == "Tu pedido fue confirmado" for m in messages.messages
    )


def test_non_whatsapp_channel_is_ignored():
    adapter, sender, _ = _adapter(user_message_at=NOW - timedelta(hours=1))
    adapter.send(
        OutboundMessage(
            conversation_id="c1",
            channel="LANGSMITH",
            destination="studio-1",
            content="hola",
        )
    )
    assert sender.texts == []
    assert sender.templates == []
