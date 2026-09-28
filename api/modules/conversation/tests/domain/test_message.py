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


def test_author_defaults_from_the_role():
    from modules.conversation.domain.models.message import Message
    from modules.conversation.domain.value_objects import MessageAuthor, MessageRole

    client_message = Message(
        message_id="msg-1", conversation_id="conv-1", role=MessageRole.USER, content="Hola"
    )
    agent_message = Message(
        message_id="msg-2", conversation_id="conv-1", role=MessageRole.AGENT, content="Hola"
    )

    assert client_message.author is MessageAuthor.CLIENT
    assert agent_message.author is MessageAuthor.AGENT


def test_author_distinguishes_a_human_operator_from_the_agent():
    from modules.conversation.domain.models.message import Message
    from modules.conversation.domain.value_objects import MessageAuthor, MessageRole

    message = Message(
        message_id="msg-1",
        conversation_id="conv-1",
        role=MessageRole.AGENT,
        content="Te atiende Facundo del local",
        author=MessageAuthor.OPERATOR,
    )

    # An operator speaks on the business side: AGENT role (the LLM sees its own
    # past turns), OPERATOR author (the panel shows a human wrote it).
    assert message.role is MessageRole.AGENT
    assert message.author is MessageAuthor.OPERATOR


def test_a_client_authored_message_must_have_the_user_role():
    from modules.conversation.domain.errors import MessageValidationError
    from modules.conversation.domain.models.message import Message
    from modules.conversation.domain.value_objects import MessageAuthor, MessageRole

    with pytest.raises(MessageValidationError):
        Message(
            message_id="msg-1",
            conversation_id="conv-1",
            role=MessageRole.AGENT,
            content="Hola",
            author=MessageAuthor.CLIENT,
        )


def test_message_rejects_an_unknown_author():
    from modules.conversation.domain.errors import MessageValidationError
    from modules.conversation.domain.models.message import Message

    with pytest.raises(MessageValidationError):
        Message(
            message_id="msg-1",
            conversation_id="conv-1",
            role="USER",
            content="Hola",
            author="ROBOT",
        )
