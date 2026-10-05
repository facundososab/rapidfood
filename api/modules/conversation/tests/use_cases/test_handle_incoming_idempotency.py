from datetime import datetime, timezone

from modules.conversation.application.use_cases.handle_incoming_message import (
    HandleIncomingMessageCommand,
    HandleIncomingMessageUseCase,
)
from modules.conversation.domain.models.agent_execution_context import (
    AgentExecutionContext,
)
from modules.conversation.domain.models.conversation import Conversation
from modules.conversation.tests.fakes import (
    InMemoryConversationRepository,
    InMemoryMessageRepository,
)

NOW = datetime(2026, 10, 2, 12, 0, tzinfo=timezone.utc)


class CountingRunner:
    def __init__(self):
        self.calls = 0

    def run(self, turn):
        self.calls += 1
        return f"reply {self.calls}"


class FixedClock:
    def now(self):
        return NOW


def _context(external_message_id="wamid.ABC"):
    return AgentExecutionContext(
        business_configuration_id="biz-1",
        conversation_id="conv-1",
        channel="WHATSAPP",
        external_thread_id="5491100000000",
        external_message_id=external_message_id,
    )


def test_a_retry_does_not_rerun_the_agent():
    messages = InMemoryMessageRepository()
    runner = CountingRunner()
    use_case = HandleIncomingMessageUseCase(messages, runner, FixedClock())

    first = use_case.execute(
        HandleIncomingMessageCommand(context=_context(), content="Quiero una pizza")
    )
    second = use_case.execute(
        HandleIncomingMessageCommand(context=_context(), content="Quiero una pizza")
    )

    assert first.already_processed is False
    assert second.already_processed is True
    assert second.response == ""
    assert runner.calls == 1
    # exactly one USER + one ASSISTANT, no duplicates
    assert len(messages.messages) == 2


def test_distinct_messages_are_processed_separately():
    messages = InMemoryMessageRepository()
    runner = CountingRunner()
    use_case = HandleIncomingMessageUseCase(messages, runner, FixedClock())

    use_case.execute(
        HandleIncomingMessageCommand(context=_context("wamid.1"), content="hola")
    )
    use_case.execute(
        HandleIncomingMessageCommand(context=_context("wamid.2"), content="otra")
    )

    assert runner.calls == 2
    assert len(messages.messages) == 4


def test_paused_conversation_skips_the_agent_but_persists_the_message():
    """Human takeover is a CORE policy: every channel gets the same behavior."""
    conversations = InMemoryConversationRepository()
    conversations.create(
        Conversation(
            conversation_id="conv-1",
            channel="WHATSAPP",
            external_thread_id="5491100000000",
            business_config_id="biz-1",
            agent_paused=True,
        )
    )
    messages = InMemoryMessageRepository()
    runner = CountingRunner()
    use_case = HandleIncomingMessageUseCase(
        messages, runner, FixedClock(), conversation_repository=conversations
    )

    result = use_case.execute(
        HandleIncomingMessageCommand(context=_context(), content="hola")
    )

    assert result.paused is True
    assert result.response == ""
    assert runner.calls == 0  # the agent never ran
    assert len(messages.messages) == 1  # only the USER message is stored
