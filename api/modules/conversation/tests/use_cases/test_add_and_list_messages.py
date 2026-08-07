from datetime import datetime, timezone


def test_add_message_returns_plain_dto_and_list_is_chronological():
    from api.modules.conversation.application.ports.driver.conversation_commands import (
        AddMessageCommand,
        ListMessagesQuery,
    )
    from api.modules.conversation.application.use_cases.add_message import AddMessageUseCase
    from api.modules.conversation.application.use_cases.list_messages import ListMessagesUseCase
    from api.modules.conversation.domain.value_objects import MessageRole, MessageStatus, Sentiment

    class MessageRepo:
        def __init__(self):
            self.messages = []

        def add(self, message):
            self.messages.append(message)
            return message

        def list_by_conversation(self, conversation_id: str):
            return list(self.messages)

    class Clock:
        def __init__(self):
            self.values = [
                datetime(2026, 1, 1, 12, 0, tzinfo=timezone.utc),
                datetime(2026, 1, 1, 12, 1, tzinfo=timezone.utc),
            ]

        def now(self):
            return self.values.pop(0)

    repo = MessageRepo()
    add_message = AddMessageUseCase(message_repository=repo, clock=Clock())

    first = add_message.execute(
        AddMessageCommand(
            message_id="msg-1",
            conversation_id="conv-1",
            role=MessageRole.USER,
            content="Hola",
            status=MessageStatus.RECEIVED,
            sentiment=Sentiment.NEUTRAL,
        )
    )
    second = add_message.execute(
        AddMessageCommand(
            message_id="msg-2",
            conversation_id="conv-1",
            role=MessageRole.AGENT,
            content="Hola, ¿en qué te ayudo?",
            status=MessageStatus.PROCESSED,
            sentiment=Sentiment.POSITIVE,
        )
    )

    listed = ListMessagesUseCase(message_repository=repo).execute(ListMessagesQuery(conversation_id="conv-1"))

    assert first.message_id == "msg-1"
    assert second.message_id == "msg-2"
    assert [message.message_id for message in listed.messages] == ["msg-1", "msg-2"]
