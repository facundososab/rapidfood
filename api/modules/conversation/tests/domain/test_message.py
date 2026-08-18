import pytest


def test_message_requires_conversation_id_and_content():
    from modules.conversation.domain.errors import MessageValidationError
    from modules.conversation.domain.models.message import Message

    with pytest.raises(MessageValidationError):
        Message(message_id="msg-1", conversation_id="", role="USER", content="Hola")

    with pytest.raises(MessageValidationError):
        Message(message_id="msg-1", conversation_id="conv-1", role="USER", content="")


def test_message_rejects_invalid_role_status_and_intent():
    from modules.conversation.domain.errors import MessageValidationError
    from modules.conversation.domain.models.message import Message

    with pytest.raises(MessageValidationError):
        Message(message_id="msg-1", conversation_id="conv-1", role="BOT", content="Hola")

    with pytest.raises(MessageValidationError):
        Message(message_id="msg-1", conversation_id="conv-1", role="USER", content="Hola", status="PENDING")

    with pytest.raises(MessageValidationError):
        Message(
            message_id="msg-1",
            conversation_id="conv-1",
            role="USER",
            content="Hola",
            detected_intent="WRONG",
        )


def test_message_accepts_valid_domain_values():
    from modules.conversation.domain.models.message import Message
    from modules.conversation.domain.value_objects import DetectedIntent, MessageRole, MessageStatus, Sentiment

    message = Message(
        message_id="msg-1",
        conversation_id="conv-1",
        role=MessageRole.USER,
        content="Quiero pedir una pizza",
        detected_intent=DetectedIntent.START_ORDER,
        sentiment=Sentiment.NEUTRAL,
        status=MessageStatus.RECEIVED,
    )

    assert message.message_id == "msg-1"
    assert message.role is MessageRole.USER
    assert message.status is MessageStatus.RECEIVED
