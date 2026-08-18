def test_get_or_create_reuses_existing_conversation():
    from modules.conversation.application.use_cases.get_or_create_conversation import (
        GetOrCreateConversationUseCase,
    )
    from modules.conversation.application.ports.driver.conversation_commands import (
        GetOrCreateConversationCommand,
    )
    from modules.conversation.domain.models.conversation import Conversation
    from modules.conversation.domain.value_objects import ConversationRecord

    class ConversationRepo:
        def __init__(self):
            self.created = False

        def find_by_channel_identity(self, channel: str, channel_identity: str):
            return ConversationRecord(conversation_id="conv-1", channel=channel, channel_identity=channel_identity)

        def create(self, conversation: Conversation):
            self.created = True
            raise AssertionError("should not create")

        def save_last_intent(self, conversation_id: str, last_intent):
            return None

    use_case = GetOrCreateConversationUseCase(conversation_repository=ConversationRepo())
    response = use_case.execute(GetOrCreateConversationCommand(channel="WHATSAPP", channel_identity="+5491112345678"))

    assert response.conversation_id == "conv-1"
    assert response.created is False


def test_get_or_create_creates_new_conversation():
    from modules.conversation.application.use_cases.get_or_create_conversation import (
        GetOrCreateConversationUseCase,
    )
    from modules.conversation.application.ports.driver.conversation_commands import (
        GetOrCreateConversationCommand,
    )

    class ConversationRepo:
        def __init__(self):
            self.created_conversation = None

        def find_by_channel_identity(self, channel: str, channel_identity: str):
            return None

        def create(self, conversation):
            self.created_conversation = conversation
            return conversation

        def save_last_intent(self, conversation_id: str, last_intent):
            return None

    repo = ConversationRepo()
    use_case = GetOrCreateConversationUseCase(conversation_repository=repo)
    response = use_case.execute(GetOrCreateConversationCommand(channel="WHATSAPP", channel_identity="+5491112345678"))

    assert response.created is True
    assert response.conversation_id
    assert repo.created_conversation.channel == "WHATSAPP"
