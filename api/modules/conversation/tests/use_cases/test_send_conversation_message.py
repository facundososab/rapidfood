from modules.conversation.application.ports.driver.whatsapp_messaging_ports import (
    SendConversationMessageCommand,
)
from modules.conversation.application.use_cases.send_conversation_message import (
    SendConversationMessageUseCase,
)
from modules.conversation.domain.models.conversation import Conversation
from modules.conversation.tests.fakes import InMemoryConversationRepository


class RecordingOutbound:
    def __init__(self):
        self.sent = []

    def send(self, message):
        self.sent.append(message)


def _conversations(conversation_id="c1", external_thread_id="5491100000000"):
    repo = InMemoryConversationRepository()
    repo.create(
        Conversation(
            conversation_id=conversation_id,
            channel="WHATSAPP",
            external_thread_id=external_thread_id,
            business_config_id="biz-1",
        )
    )
    return repo


def test_dispatches_to_the_conversations_channel():
    outbound = RecordingOutbound()
    use_case = SendConversationMessageUseCase(_conversations(), outbound)

    assert use_case.execute(SendConversationMessageCommand("c1", "Hola")) is True

    assert len(outbound.sent) == 1
    message = outbound.sent[0]
    assert message.conversation_id == "c1"
    assert message.channel == "WHATSAPP"
    assert message.destination == "5491100000000"
    assert message.content == "Hola"


def test_unknown_conversation_returns_false():
    use_case = SendConversationMessageUseCase(
        InMemoryConversationRepository(), RecordingOutbound()
    )
    assert use_case.execute(SendConversationMessageCommand("nope", "x")) is False


def test_missing_destination_returns_false():
    outbound = RecordingOutbound()
    use_case = SendConversationMessageUseCase(
        _conversations(external_thread_id=None), outbound
    )
    assert use_case.execute(SendConversationMessageCommand("c1", "x")) is False
    assert outbound.sent == []
