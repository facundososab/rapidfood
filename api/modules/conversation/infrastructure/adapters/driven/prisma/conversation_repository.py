from __future__ import annotations

from api.modules.conversation.domain.models.conversation import Conversation
from api.modules.conversation.domain.value_objects import ConversationRecord


class PrismaConversationRepository:
    def __init__(self, client):
        self._client = client

    def find_by_channel_identity(self, channel: str, channel_identity: str):
        row = self._client.conversation.find_first(where={"channel": channel, "clientId": None})
        if row is None:
            return None
        return _to_record(row)

    def create(self, conversation: Conversation):
        row = self._client.conversation.create(
            data={
                "id": conversation.conversation_id,
                "channel": conversation.channel,
                "lastIntent": conversation.last_intent.value if conversation.last_intent else None,
                "overallSentiment": conversation.overall_sentiment.value if conversation.overall_sentiment else None,
                "clientId": conversation.client_id,
            }
        )
        return _to_record(row)

    def save_last_intent(self, conversation_id: str, last_intent):
        self._client.conversation.update(where={"id": conversation_id}, data={"lastIntent": last_intent.value if last_intent else None})


def _to_record(row) -> ConversationRecord:
    return ConversationRecord(
        conversation_id=row.id,
        channel=row.channel,
        channel_identity=getattr(row, "channel_identity", None),
        client_id=getattr(row, "clientId", None),
        last_intent=getattr(row, "lastIntent", None),
        overall_sentiment=getattr(row, "overallSentiment", None),
    )
