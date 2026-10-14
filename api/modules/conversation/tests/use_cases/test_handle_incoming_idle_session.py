"""Idle-session policy: after a long gap, restart the order and greet again."""
from datetime import datetime, timedelta, timezone

from modules.conversation.application.use_cases.handle_incoming_message import (
    HandleIncomingMessageCommand,
    HandleIncomingMessageUseCase,
)
from modules.conversation.domain.models.agent_execution_context import (
    AgentExecutionContext,
)
from modules.conversation.domain.models.message import Message
from modules.conversation.domain.value_objects import MessageRole
from modules.conversation.tests.fakes import InMemoryMessageRepository

NOW = datetime(2026, 10, 14, 12, 0, tzinfo=timezone.utc)


class FixedClock:
    def now(self):
        return NOW


class CapturingRunner:
    def __init__(self):
        self.turns = []

    def run(self, turn):
        self.turns.append(turn)
        return "ok"


class RecordingOrderService:
    def __init__(self):
        self.resets = []

    def reset_active_order(self, business_config_id, conversation_id):
        self.resets.append((business_config_id, conversation_id))
        return "new-draft"


class ExplodingOrderService:
    def reset_active_order(self, business_config_id, conversation_id):
        raise RuntimeError("order module down")


def _context(external_message_id="wamid.new"):
    return AgentExecutionContext(
        business_configuration_id="biz-1",
        conversation_id="conv-1",
        channel="WHATSAPP",
        external_thread_id="5491100000000",
        external_message_id=external_message_id,
    )


def _seed(messages, *, created_at, content="hola"):
    messages.add(
        Message(
            message_id="seed-1",
            conversation_id="conv-1",
            role=MessageRole.AGENT,
            content=content,
            created_at=created_at,
        )
    )


def _use_case(messages, runner, order_service=None, *, reset_hours=2, greet_hours=12):
    return HandleIncomingMessageUseCase(
        messages,
        runner,
        FixedClock(),
        order_service=order_service,
        session_idle_after=timedelta(hours=reset_hours),
        greeting_idle_after=timedelta(hours=greet_hours),
    )


def test_idle_past_the_session_threshold_restarts_the_order_without_greeting():
    messages = InMemoryMessageRepository()
    _seed(messages, created_at=NOW - timedelta(hours=3))
    runner = CapturingRunner()
    order_service = RecordingOrderService()

    _use_case(messages, runner, order_service).execute(
        HandleIncomingMessageCommand(context=_context(), content="hola quiero pedir")
    )

    assert order_service.resets == [("biz-1", "conv-1")]
    # 3h is past the order threshold but short of the greeting window.
    assert runner.turns[0].new_session is False


def test_a_short_gap_is_a_plain_continuation():
    messages = InMemoryMessageRepository()
    _seed(messages, created_at=NOW - timedelta(minutes=30))
    runner = CapturingRunner()
    order_service = RecordingOrderService()

    _use_case(messages, runner, order_service).execute(
        HandleIncomingMessageCommand(context=_context(), content="y tambien una coca")
    )

    assert order_service.resets == []
    assert runner.turns[0].new_session is False


def test_a_long_gap_restarts_and_greets_again():
    messages = InMemoryMessageRepository()
    _seed(messages, created_at=NOW - timedelta(hours=20))
    runner = CapturingRunner()
    order_service = RecordingOrderService()

    _use_case(messages, runner, order_service).execute(
        HandleIncomingMessageCommand(context=_context(), content="hola quiero pedir")
    )

    assert order_service.resets == [("biz-1", "conv-1")]
    assert runner.turns[0].new_session is True


def test_the_first_message_is_a_new_session_without_any_reset():
    messages = InMemoryMessageRepository()
    runner = CapturingRunner()
    order_service = RecordingOrderService()

    _use_case(messages, runner, order_service).execute(
        HandleIncomingMessageCommand(context=_context(), content="hola")
    )

    assert order_service.resets == []
    assert runner.turns[0].new_session is True


def test_a_naive_previous_timestamp_is_compared_as_utc():
    messages = InMemoryMessageRepository()
    _seed(messages, created_at=(NOW - timedelta(hours=3)).replace(tzinfo=None))
    runner = CapturingRunner()
    order_service = RecordingOrderService()

    _use_case(messages, runner, order_service).execute(
        HandleIncomingMessageCommand(context=_context(), content="hola")
    )

    assert order_service.resets == [("biz-1", "conv-1")]


def test_a_reset_failure_never_breaks_the_turn():
    messages = InMemoryMessageRepository()
    _seed(messages, created_at=NOW - timedelta(hours=3))
    runner = CapturingRunner()

    result = _use_case(messages, runner, ExplodingOrderService()).execute(
        HandleIncomingMessageCommand(context=_context(), content="hola")
    )

    assert result.response == "ok"
    assert len(runner.turns) == 1
