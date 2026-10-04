"""Panel chat use cases: listing, human takeover and replying as the customer."""
from datetime import datetime, timezone

import pytest

from modules.conversation.application.use_cases.panel_conversations import (
    AppendOperatorMessageUseCase,
    GetConversationDetailUseCase,
    ListConversationsUseCase,
    ReplyAsClientForConversationUseCase,
    SetConversationTakeoverUseCase,
)
from modules.conversation.domain.errors import ConversationNotFoundError
from modules.conversation.domain.models.conversation import Conversation
from modules.conversation.tests.fakes import (
    InMemoryConversationRepository,
    InMemoryMessageRepository,
)


class FakeClock:
    def now(self):
        return datetime(2026, 9, 17, tzinfo=timezone.utc)


class FakeHandler:
    def __init__(self, response="¡Dale! ¿Algo más?", paused=False):
        self.response = response
        self.paused = paused
        self.calls = []

    def execute(self, command):
        self.calls.append(command)
        from modules.conversation.application.use_cases.handle_incoming_message import (
            HandleIncomingMessageResult,
        )

        return HandleIncomingMessageResult(
            conversation_id=command.context.conversation_id,
            user_message_id="u-1",
            assistant_message_id="a-1",
            response="" if self.paused else self.response,
            paused=self.paused,
        )


def _repos():
    conversations = InMemoryConversationRepository()
    messages = InMemoryMessageRepository()
    conversation = conversations.create(
        Conversation(
            conversation_id="conv-1",
            channel="LANGSMITH",
            external_thread_id="thread-1",
            business_config_id="biz-1",
        )
    )
    return conversations, messages, conversation


def test_list_conversations_reports_last_message_and_state():
    conversations, messages, _ = _repos()
    from modules.conversation.domain.models.message import Message
    from modules.conversation.domain.value_objects import MessageRole

    messages.add(
        Message(
            message_id="m-1",
            conversation_id="conv-1",
            role=MessageRole.USER,
            content="hola",
            created_at=FakeClock().now(),
        )
    )

    summaries = ListConversationsUseCase(conversations, messages).execute()

    assert len(summaries) == 1
    summary = summaries[0]
    assert summary.conversation_id == "conv-1"
    assert summary.channel == "LANGSMITH"
    assert summary.external_thread_id == "thread-1"
    assert summary.agent_paused is False
    assert summary.message_count == 1
    assert summary.last_message == "hola"


def test_operator_message_is_persisted_as_a_human_on_the_business_side():
    conversations, messages, _ = _repos()
    use_case = AppendOperatorMessageUseCase(conversations, messages, FakeClock())

    detail = use_case.execute("conv-1", "Te atiende Facundo del local")

    assert [m.role for m in detail.messages] == ["AGENT"]
    assert [m.author for m in detail.messages] == ["OPERATOR"]
    assert detail.messages[0].content == "Te atiende Facundo del local"


def test_agent_ed_message_is_attributed_to_the_agent():
    conversations, messages, _ = _repos()
    from modules.conversation.domain.models.message import Message
    from modules.conversation.domain.value_objects import MessageRole

    messages.add(
        Message(
            message_id="m-1",
            conversation_id="conv-1",
            role=MessageRole.AGENT,
            content="¡Listo!",
            created_at=FakeClock().now(),
        )
    )

    detail = GetConversationDetailUseCase(conversations, messages).execute("conv-1")

    assert [m.role for m in detail.messages] == ["AGENT"]
    assert [m.author for m in detail.messages] == ["AGENT"]


def test_operator_message_on_an_unknown_conversation_fails():
    conversations, messages, _ = _repos()
    use_case = AppendOperatorMessageUseCase(conversations, messages, FakeClock())

    with pytest.raises(ConversationNotFoundError):
        use_case.execute("missing", "hola")


def test_reply_as_client_runs_the_agent_when_not_paused():
    conversations, messages, _ = _repos()
    handler = FakeHandler()
    use_case = ReplyAsClientForConversationUseCase(
        conversations, messages, handler, FakeClock()
    )

    result = use_case.execute("conv-1", "quiero una doble")

    assert result.paused is False
    assert result.response == "¡Dale! ¿Algo más?"
    assert len(handler.calls) == 1
    context = handler.calls[0].context
    assert context.business_configuration_id == "biz-1"
    assert context.external_thread_id == "thread-1"
    assert context.external_message_id  # stable per ingress


def test_reply_as_client_reflects_a_paused_core_result():
    """Pause is the CORE's policy; the panel only reflects it and does not send."""
    conversations, messages, _ = _repos()
    handler = FakeHandler(paused=True)
    sender = RecordingSender()
    use_case = ReplyAsClientForConversationUseCase(
        conversations, messages, handler, FakeClock(), send_message=sender
    )

    result = use_case.execute("conv-1", "hola?")

    assert result.paused is True
    assert result.response is None
    assert handler.calls  # the panel delegated to the core use case
    assert sender.sent == []  # no reply delivered while paused


def test_takeover_toggles_the_flag_and_returns_the_thread():
    conversations, messages, _ = _repos()
    use_case = SetConversationTakeoverUseCase(conversations, messages)

    taken = use_case.execute("conv-1", True)
    assert taken.agent_paused is True
    released = use_case.execute("conv-1", False)
    assert released.agent_paused is False


def test_detail_of_an_unknown_conversation_fails():
    conversations, messages, _ = _repos()
    with pytest.raises(ConversationNotFoundError):
        GetConversationDetailUseCase(conversations, messages).execute("missing")


class RecordingSender:
    def __init__(self):
        self.sent = []

    def execute(self, command):
        self.sent.append((command.conversation_id, command.content))
        return True


def test_operator_message_is_delivered_to_the_channel():
    conversations, messages, _ = _repos()
    sender = RecordingSender()
    use_case = AppendOperatorMessageUseCase(
        conversations, messages, FakeClock(), send_message=sender
    )

    use_case.execute("conv-1", "Hola, soy el local")

    assert sender.sent == [("conv-1", "Hola, soy el local")]


def test_reply_as_client_delivers_the_agent_response():
    conversations, messages, _ = _repos()
    sender = RecordingSender()
    use_case = ReplyAsClientForConversationUseCase(
        conversations, messages, FakeHandler("Listo"), FakeClock(), send_message=sender
    )

    result = use_case.execute("conv-1", "quiero una pizza")

    assert result.response == "Listo"
    assert sender.sent == [("conv-1", "Listo")]
