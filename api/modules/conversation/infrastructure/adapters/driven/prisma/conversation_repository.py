from __future__ import annotations

from modules.conversation.domain.models.conversation import Conversation
from modules.conversation.domain.value_objects import ConversationRecord


class PrismaConversationRepository:
    def __init__(self, client=None):
        # Resolved lazily so constructing the container never opens a connection.
        self._client = client

    @property
    def _db(self):
        if self._client is not None:
            return self._client
        from shared.infrastructure.prisma.db import db

        return db.client

    def find_by_thread(
        self, business_config_id: str, channel: str, external_thread_id: str
    ) -> ConversationRecord | None:
        row = self._db.conversation.find_first(
            where={
                "businessConfigId": business_config_id,
                "channel": channel,
                "externalThreadId": external_thread_id,
            }
        )
        if row is None:
            return None
        return _to_record(row)

    def get_by_id(self, conversation_id: str) -> ConversationRecord | None:
        row = self._db.conversation.find_unique(where={"id": conversation_id})
        if row is None:
            return None
        return _to_record(row)

    def list_conversations(self) -> list[ConversationRecord]:
        rows = self._db.conversation.find_many(order={"id": "desc"})
        return [_to_record(row) for row in rows]

    def set_agent_paused(self, conversation_id: str, paused: bool) -> None:
        self._db.conversation.update(
            where={"id": conversation_id}, data={"agentPaused": bool(paused)}
        )

    def find_by_channel_identity(self, channel: str, channel_identity: str):
        # Legacy channel-identity lookup kept for the deterministic scaffold.
        row = self._db.conversation.find_first(
            where={"channel": channel, "clientId": None}
        )
        if row is None:
            return None
        return _to_record(row)

    def create(self, conversation: Conversation):
        row = self._db.conversation.create(
            data={
                "id": conversation.conversation_id,
                "channel": conversation.channel,
                "externalThreadId": conversation.external_thread_id,
                "businessConfigId": conversation.business_config_id,
                "lastIntent": conversation.last_intent.value if conversation.last_intent else None,
                "overallSentiment": conversation.overall_sentiment.value if conversation.overall_sentiment else None,
                "clientId": conversation.client_id,
                "agentPaused": conversation.agent_paused,
            }
        )
        return _to_record(row)

    def save_last_intent(self, conversation_id: str, last_intent):
        self._db.conversation.update(
            where={"id": conversation_id},
            data={"lastIntent": last_intent.value if last_intent else None},
        )


def _to_record(row) -> ConversationRecord:
    return ConversationRecord(
        conversation_id=row.id,
        channel=row.channel,
        channel_identity=getattr(row, "channel_identity", None),
        client_id=getattr(row, "clientId", None),
        last_intent=getattr(row, "lastIntent", None),
        overall_sentiment=getattr(row, "overallSentiment", None),
        external_thread_id=getattr(row, "externalThreadId", None),
        business_config_id=getattr(row, "businessConfigId", None),
        agent_paused=bool(getattr(row, "agentPaused", False)),
    )
