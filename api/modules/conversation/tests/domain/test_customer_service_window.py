from datetime import datetime, timedelta, timezone

from modules.conversation.domain.models.message import Message
from modules.conversation.domain.services.customer_service_window import (
    is_customer_service_window_open,
)
from modules.conversation.domain.value_objects import MessageRole

NOW = datetime(2026, 10, 2, 12, 0, tzinfo=timezone.utc)


def _message(role, created_at, content="hola"):
    return Message(
        message_id=f"m-{created_at.timestamp()}-{role}",
        conversation_id="c1",
        role=role,
        content=content,
        created_at=created_at,
    )


def test_no_customer_message_means_closed():
    assert is_customer_service_window_open([], NOW) is False


def test_recent_customer_message_keeps_the_window_open():
    messages = [_message(MessageRole.USER, NOW - timedelta(hours=1))]
    assert is_customer_service_window_open(messages, NOW) is True


def test_window_is_closed_after_24_hours():
    messages = [_message(MessageRole.USER, NOW - timedelta(hours=25))]
    assert is_customer_service_window_open(messages, NOW) is False


def test_latest_customer_message_resets_the_window():
    messages = [
        _message(MessageRole.USER, NOW - timedelta(hours=30)),
        _message(MessageRole.AGENT, NOW - timedelta(hours=2)),
        _message(MessageRole.USER, NOW - timedelta(hours=1)),
    ]
    assert is_customer_service_window_open(messages, NOW) is True


def test_agent_messages_do_not_open_the_window():
    messages = [_message(MessageRole.AGENT, NOW - timedelta(minutes=5))]
    assert is_customer_service_window_open(messages, NOW) is False
