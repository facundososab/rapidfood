"""Channel thread -> Conversation resolution."""
from modules.conversation.application.use_cases.resolve_conversation_for_channel import (
    ResolveConversationCommand,
    ResolveConversationForChannelUseCase,
)
from modules.conversation.domain.models.conversation import Conversation


class FakeConversationRepository:
    def __init__(self):
        self.rows = {}
        self.last_intent = {}

    def find_by_thread(self, business_config_id, channel, external_thread_id):
        return self.rows.get((business_config_id, channel, external_thread_id))

    def find_by_channel_identity(self, channel, channel_identity):
        return None

    def create(self, conversation):
        self.rows[
            (
                conversation.business_config_id,
                conversation.channel,
                conversation.external_thread_id,
            )
        ] = conversation
        return conversation

    def save_last_intent(self, conversation_id, last_intent):
        self.last_intent[conversation_id] = last_intent


def _command(**overrides):
    values = dict(
        business_config_id="biz-1",
        channel="LANGSMITH",
        external_thread_id="thread-1",
        client_id="client-1",
    )
    values.update(overrides)
    return ResolveConversationCommand(**values)


def test_same_thread_resolves_to_the_same_conversation():
    repo = FakeConversationRepository()
    use_case = ResolveConversationForChannelUseCase(repo)

    first = use_case.execute(_command())
    second = use_case.execute(_command())

    assert first.created is True
    assert second.created is False
    assert first.conversation_id == second.conversation_id


def test_different_threads_map_to_different_conversations():
    repo = FakeConversationRepository()
    use_case = ResolveConversationForChannelUseCase(repo)

    first = use_case.execute(_command(external_thread_id="thread-1"))
    second = use_case.execute(_command(external_thread_id="thread-2"))

    assert first.conversation_id != second.conversation_id


def test_the_same_thread_in_another_business_is_a_different_conversation():
    repo = FakeConversationRepository()
    use_case = ResolveConversationForChannelUseCase(repo)

    first = use_case.execute(_command(business_config_id="biz-1"))
    second = use_case.execute(_command(business_config_id="biz-2"))

    assert first.conversation_id != second.conversation_id


def test_the_internal_id_is_not_the_external_thread_id():
    repo = FakeConversationRepository()
    use_case = ResolveConversationForChannelUseCase(repo)

    result = use_case.execute(_command(external_thread_id="thread-1"))

    assert result.conversation_id != "thread-1"
    assert len(result.conversation_id) == 36  # a UUID


def test_client_is_kept_from_the_resolution():
    repo = FakeConversationRepository()
    use_case = ResolveConversationForChannelUseCase(repo)

    result = use_case.execute(_command(client_id="client-9"))

    assert result.client_id == "client-9"
