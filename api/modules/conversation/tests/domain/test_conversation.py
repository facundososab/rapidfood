import pytest


def test_conversation_rejects_empty_id_and_channel():
    from modules.conversation.domain.errors import ConversationValidationError
    from modules.conversation.domain.models.conversation import Conversation

    with pytest.raises(ConversationValidationError):
        Conversation(conversation_id="", channel="WHATSAPP")

    with pytest.raises(ConversationValidationError):
        Conversation(conversation_id="conv-1", channel="")


def test_conversation_accepts_valid_last_intent_and_sentiment():
    from modules.conversation.domain.models.conversation import Conversation
    from modules.conversation.domain.value_objects import DetectedIntent, Sentiment

    conversation = Conversation(
        conversation_id="conv-1",
        channel="WHATSAPP",
        last_intent=DetectedIntent.START_ORDER,
        overall_sentiment=Sentiment.POSITIVE,
    )

    assert conversation.conversation_id == "conv-1"
    assert conversation.last_intent is DetectedIntent.START_ORDER
    assert conversation.overall_sentiment is Sentiment.POSITIVE


def test_conversation_rejects_invalid_last_intent():
    from modules.conversation.domain.errors import ConversationValidationError
    from modules.conversation.domain.models.conversation import Conversation

    with pytest.raises(ConversationValidationError):
        Conversation(conversation_id="conv-1", channel="WHATSAPP", last_intent="oops")
