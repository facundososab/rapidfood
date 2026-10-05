from __future__ import annotations

from modules.conversation.domain.models.message import Message


class PrismaMessageRepository:
    def __init__(self, client=None):
        # Resolved lazily so constructing the container never opens a connection.
        self._client = client

    @property
    def _db(self):
        if self._client is not None:
            return self._client
        from shared.infrastructure.prisma.db import db

        return db.client

    def add(self, message: Message) -> Message:
        # Idempotent by message id: a retry of the same ingress message returns
        # the stored row instead of raising a unique violation.
        existing = self._db.message.find_unique(where={"id": message.message_id})
        if existing is not None:
            return message

        self._db.message.create(
            data={
                "id": message.message_id,
                "conversationId": message.conversation_id,
                "role": message.role.value,
                "author": message.author.value if message.author else None,
                "content": message.content,
                "detectedIntent": message.detected_intent.value if message.detected_intent else None,
                "sentiment": message.sentiment.value if message.sentiment else None,
                "status": message.status.value if message.status else None,
                "createdAt": message.created_at,
            }
        )
        return message

    def find_by_id(self, message_id: str) -> Message | None:
        row = self._db.message.find_unique(where={"id": message_id})
        return _to_message(row) if row is not None else None

    def list_by_conversation(self, conversation_id: str) -> list[Message]:
        rows = self._db.message.find_many(where={"conversationId": conversation_id}, order={"createdAt": "asc"})
        return [_to_message(row) for row in rows]


def _to_message(row) -> Message:
    return Message(
        message_id=row.id,
        conversation_id=row.conversationId,
        role=row.role,
        author=getattr(row, "author", None),
        content=row.content,
        detected_intent=getattr(row, "detectedIntent", None),
        sentiment=getattr(row, "sentiment", None),
        status=getattr(row, "status", None),
        created_at=getattr(row, "createdAt", None),
    )
